import datetime

import aiohttp
import discord
from discord.ext import commands
from PIL import Image
import io
import numpy as np
import dotenv
import os

dotenv.load_dotenv()

TOKEN: str = os.getenv('TOKEN')
REFERENCE_IMAGE_PATH: str = 'reference_image.jpg'
THRESHOLD: float = 0.9  # Adjust this threshold based on your needs

intents = discord.Intents.all()
intents.messages = True

bot: commands.Bot = commands.Bot(command_prefix='!', intents=intents)
# aiohttp_session = None

@bot.event
async def on_ready() -> None:
    print(f'We have logged in as {bot.user.name}')


@bot.event
async def on_message(message: discord.Message) -> None:

    print(f"Got message in {message.channel.name}!")
    if message.author == bot.user:
        return

    if message.embeds:
        embed = message.embeds[0].image

    imgs = []
    if message.embeds:
        reference_image: Image.Image = Image.open(REFERENCE_IMAGE_PATH)
        imgs = await get_embedded_images(message)
        for img_bytes in imgs:
            user_image: Image.Image = Image.open(io.BytesIO(img_bytes))
            user_image, reference_image = resize_images(user_image, reference_image)

            similarity_score = image_similarity(reference_image, user_image)
            if similarity_score > THRESHOLD:
                await timeout_user(message.author, message.channel)
                break
            else:
                print("Got image with similarity ==", similarity_score)

    if len(imgs) == 0 and message.attachments and 'image' in message.attachments[0].content_type:
        print("Got Image!")
        reference_image: Image.Image = Image.open(REFERENCE_IMAGE_PATH)

        attachment_bytes: bytes = await message.attachments[0].read()
        user_image: Image.Image = Image.open(io.BytesIO(attachment_bytes))

        user_image, reference_image = resize_images(user_image, reference_image)

        similarity_score = image_similarity(reference_image, user_image)
        if similarity_score > THRESHOLD:
            await timeout_user(message.author, message.channel)

        else:
            print("Got image with similarity ==", similarity_score)

    await bot.process_commands(message)


async def download_image(url: str) -> bytes:
    aiohttp_session = aiohttp.ClientSession()
    async with aiohttp_session.get(url) as response:
        return await response.read()

def resize_images(image1: Image.Image, image2: Image.Image) -> tuple[Image.Image, Image.Image]:
    width1, height1 = image1.size
    width2, height2 = image2.size

    image1.save("IMAGE_1.jpg")
    image2.save("IMAGE_2.jpg")
    if width1 * height1 > width2 * height2:
        image1 = image1.resize((width2, height2))
    else:
        image2 = image2.resize((width1, height1))

    image1.save("IMAGE_1r.jpg")
    image2.save("IMAGE_2r.jpg")
    return image1, image2


def image_similarity(image1: Image.Image, image2: Image.Image) -> float:
    array1: np.ndarray = np.array(image1)
    array2: np.ndarray = np.array(image2)

    mse: float = np.sum((array1 - array2) ** 2) / float(array1.shape[0] * array1.shape[1])
    similarity: float = 1 - (mse / (255**2))

    return similarity


async def timeout_user(member: discord.Member, channel: discord.TextChannel):
    duration = datetime.timedelta(seconds=0, minutes=5, hours=0, days=0)
    try:
        await member.timeout(duration, reason="Your loneliness has been cured.")
    except Exception as e:
        print(e)
    await channel.send(f'{member.mention} has been cured of loneliness for {duration}')


async def get_embedded_images(message: discord.Message) -> list[bytes]:
    embedded_images = []

    for embed in message.embeds:
        if embed.type == 'image':
            if embed.thumbnail and embed.thumbnail.proxy_url:
                image_url = embed.thumbnail.proxy_url
                image_bytes = await download_image(image_url)
                embedded_images.append(image_bytes)

    return embedded_images

bot.run(TOKEN)