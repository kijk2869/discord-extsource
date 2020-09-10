import discord

import discord_extsource

Source = None

app = discord.Client()


@app.event
async def on_message(message):
    global Source
    if message.content.startswith("testplay"):
        await message.author.voice.channel.connect()
        Source = await discord_extsource.YTDLSource.create(message.content[8:].strip())
        print(Source.title)
        message.guild.voice_client.play(Source)

    if message.content.startswith("testseek"):
        await Source.seek(float(message.content[8:].strip()))


app.run("NTAyNDczMzI1OTY1MjEzNzE4.W8iKwA.B6IE43XAoAFvfPSFYJz5SMPWAn4")
