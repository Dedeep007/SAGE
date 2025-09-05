"""
Simple test for voice functionality
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.voice_processor import VoiceProcessor

async def test_voice():
    try:
        print("Initializing voice processor...")
        voice = VoiceProcessor()
        
        print("Testing speech...")
        await voice.speak_text("Hello! This is a test of the voice system.", use_gtts=False)
        
        print("Voice test completed!")
        
    except Exception as e:
        print(f"Voice test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_voice())
