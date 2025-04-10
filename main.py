import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import json
import os


# .env読み込み
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Bot設定
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

# 許可されている部屋番号
VALID_ROOMS = [
    f"{c}-{i}" for c in ["A", "B", "C", "D", "E", "F", "G", "H"] for i in range(1, 16)
]

# リザルト保存ファイル
RESULTS_FILE = "results.json"

# 初期化（ファイルが無ければ作成）
if not os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

# /result コマンド
@bot.tree.command(name="result", description="勝利したプレイヤーが試合結果を登録します。")
@app_commands.describe(
    room="部屋番号（例: 3-A）",
    uma="使用したウマ娘名",
    opponent="対戦相手の名前（カンマ区切りで複数名）"
)
async def result(interaction: discord.Interaction, room: str, uma: str, opponent: str):
    room = room.upper()

    if room not in VALID_ROOMS:
        await interaction.response.send_message(f"❌ 部屋番号「{room}」は無効です。正しい部屋番号を入力してください。", ephemeral=True)
        return

    # リザルト読み込み
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        results = json.load(f)

    # 重複チェック（同じ部屋に既に登録されている）
    if any(r["room"] == room for r in results):
        await interaction.response.send_message(f"⚠️ 部屋「{room}」にはすでに結果が登録されています。", ephemeral=True)
        return

    # 対戦相手をカンマで分割し、リストに変換
    opponent_list = [op.strip() for op in opponent.split(",")]

    # 登録
    result_entry = {
        "room": room,
        "winner": interaction.user.name,
        "opponent": opponent_list,  # 複数名の対戦相手をリストとして保存
        "uma": uma,
    }

    results.append(result_entry)

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 対戦相手を表示用にカンマ区切りでフォーマット
    opponent_display = ", ".join(opponent_list)

    await interaction.response.send_message(
        f"✅ 試合結果を登録しました！\n部屋: {room}\n勝者: {interaction.user.mention}\nウマ娘: {uma}\n対戦相手: {opponent_display}"
    )

# /results コマンド
@bot.tree.command(name="results", description="登録された試合結果一覧を表示します（運営用）")
async def results(interaction: discord.Interaction):
    # 管理者チェック
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ このコマンドは管理者のみが使用できます。", ephemeral=True)
        return

    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        results = json.load(f)

    if not results:
        await interaction.response.send_message("⚠️ まだ試合結果は登録されていません。", ephemeral=True)
        return

    embed = discord.Embed(title="📊 試合結果一覧", color=0x00bfff)

    for entry in results:
        opponent_display = ", ".join(entry['opponent'])  # 複数名の対戦相手をカンマ区切りで表示

        embed.add_field(
            name=f"部屋: {entry['room']}",
            value=f"👑 勝者: **{entry['winner']}**\n🐎 ウマ娘: {entry['uma']}\n👤 対戦相手: **{opponent_display}**",
            inline=False
        )

    await interaction.response.send_message(embed=embed)

# /delete_result コマンド（管理者専用）
@bot.tree.command(name="delete_result", description="指定した部屋の試合結果を削除します（管理者専用）")
@app_commands.describe(
    room="削除したい部屋番号（例: 3-A）"
)
async def delete_result(interaction: discord.Interaction, room: str):
    room = room.upper()

    # 管理者チェック
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ このコマンドは管理者のみが使用できます。", ephemeral=True)
        return

    # リザルト読み込み
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        results = json.load(f)

    # 指定部屋の結果を削除
    new_results = [r for r in results if r["room"] != room]

    if len(results) == len(new_results):
        await interaction.response.send_message(f"⚠️ 部屋「{room}」の試合結果は見つかりませんでした。", ephemeral=True)
        return

    # 上書き保存
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(new_results, f, ensure_ascii=False, indent=2)

    await interaction.response.send_message(f"🗑️ 部屋「{room}」の試合結果を削除しました。", ephemeral=True)

# Bot起動時にスラッシュコマンド同期
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ スラッシュコマンドを {len(synced)} 件同期しました。")
    except Exception as e:
        print(f"❌ コマンド同期失敗: {e}")

    print(f"Botログイン完了: {bot.user}")

# 実行
bot.run(TOKEN)
