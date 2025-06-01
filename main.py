import os
import discord
from discord.ext import commands
from discord import app_commands
import time
import sys

# ▶ 환경 변수로 토큰 불러오기
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    print("❗ 환경 변수 DISCORD_BOT_TOKEN이 설정되지 않았습니다.")
    sys.exit(1)

# ▶ (선택) 디버그용: 읽어온 토큰 정보 확인
print(f"🔍 읽어온 토큰(repr): {repr(TOKEN)}")
print(f"🔢 토큰 길이: {len(TOKEN)} 자")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# 구인 명령어를 허용할 텍스트 채널 ID 목록
ALLOWED_TEXT_CHANNEL_IDS = [
    758040017439293501,  # 필요 시 채널 ID를 추가
]

# 쿨타임 저장용 딕셔너리
cooldowns = {}

class RecruitView(discord.ui.View):
    def __init__(self, invite_url: str):
        super().__init__()
        self.add_item(
            discord.ui.Button(
                label="🎧 음성 채널 입장하기",
                style=discord.ButtonStyle.link,
                url=invite_url
            )
        )

@bot.event
async def on_ready():
    print(f'✅ 봇 실행됨: {bot.user} (ID: {bot.user.id})')
    try:
        synced = await bot.tree.sync()
        print(f'📌 슬래시 명령어 동기화 완료 ({len(synced)}개)')
    except Exception as e:
        print(f'⚠️ 슬래시 명령어 동기화 중 오류 발생: {e}')

@bot.tree.command(name="구인", description="현재 음성 채널 기준으로 구인 공고를 작성합니다.")
@app_commands.describe(description="설명")
@app_commands.rename(description="설명")
async def recruit(interaction: discord.Interaction, description: str):
    MAXIMUM = 4
    user_id = interaction.user.id
    now = time.time()

    # 허용된 텍스트 채널에서만 명령어 사용 가능
    if interaction.channel.id not in ALLOWED_TEXT_CHANNEL_IDS:
        await interaction.response.send_message(
            "❗ 이 명령어는 지정된 텍스트 채널에서만 사용할 수 있습니다.",
            ephemeral=True
        )
        return

    # 쿨타임 체크 (60초)
    if user_id in cooldowns and now - cooldowns[user_id] < 60:
        remain = int(60 - (now - cooldowns[user_id]))
        await interaction.response.send_message(
            f"⏱️ 쿨타임이 적용되어 있습니다. {remain}초 후에 다시 시도해주세요.",
            ephemeral=True
        )
        return

    # 유저가 음성 채널에 접속했는지 확인
    voice_state = interaction.user.voice
    if not voice_state or not voice_state.channel:
        await interaction.response.send_message(
            "❗ 먼저 음성 채널에 접속해 주세요.",
            ephemeral=True
        )
        return

    voice_channel = voice_state.channel
    # 봇을 제외한 실제 유저만 카운트
    members = [m for m in voice_channel.members if not m.bot]
    current_count = len(members)

    # 최대 인원 초과 시
    if current_count > MAXIMUM:
        await interaction.response.send_message(
            f"❗ 현재 인원 수가 최대 인원({MAXIMUM}명)을 초과했습니다. ({current_count}명 접속 중)",
            ephemeral=True
        )
        return

    # 카테고리 이름 (없으면 "기타")
    category_name = voice_channel.category.name if voice_channel.category else "기타"
    # 초대 코드 생성 (5분 유지, 최대 5회 사용)
    invite = await voice_channel.create_invite(max_age=300, max_uses=5, unique=True)

    # 임베드 생성
    embed = discord.Embed(
        title="📢 구인 공고",
        description=f"{interaction.user.mention} 님이 멤버를 모집 중입니다!",
        color=discord.Color.green()
    )
    embed.add_field(name="카테고리", value=f"【 {category_name} 】", inline=False)
    embed.add_field(name="채널명", value=f"[{voice_channel.name}]({invite.url})", inline=True)
    embed.add_field(name="멤버 수", value=f"{current_count}명 / {MAXIMUM}명", inline=True)
    embed.add_field(name="설명", value=description, inline=False)

    view = RecruitView(invite.url)

    await interaction.response.send_message(
        embed=embed,
        view=view
    )

    # 쿨타임 갱신
    cooldowns[user_id] = now

# 봇 실행
bot.run(TOKEN)
