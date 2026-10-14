import asyncio
import edge_tts

async def main():
    voice = "en-US-JennyNeural" # Warm, soothing, gentle female voice
    text = "Twinkle, twinkle, little star, how I wonder what you are."
    communicate = edge_tts.Communicate(text, voice, rate="-18%", pitch="+4Hz")
    await communicate.save("test_voice.mp3")
    print("Voice OK!")

if __name__ == "__main__":
    asyncio.run(main())
