import re
import discord
from discord import PartialEmoji

async def decodeEmoji(rawEmoji: str):
    try:
        if rawEmoji.startswith("\\x") or rawEmoji.startswith("U+") or rawEmoji.startswith("\\u"):
            return rawEmoji
        # Convert emoji into its Unicode codepoint (like \U0001f7e6 for 🟦)
        codepoint = rawEmoji.encode("unicode-escape").decode("ascii")
        formatted_codepoint = codepoint.replace("\\U", "\\u").lower()
        formatted_codepoint = formatted_codepoint.replace("\\ufe0f", "").lower()
        return formatted_codepoint
    except Exception as e:
        return rawEmoji
async def encodeEmoji(codepoint: str):
    try:
        if all(ord(c) < 128 for c in codepoint):
            if codepoint.startswith("\\U") or codepoint.startswith("\\u") or codepoint.startswith("\\x"):
                return bytes(codepoint, "utf-8").decode("unicode_escape")
        return codepoint
    except Exception as e:
        return codepoint
    
def normalizeEmoji(emoji: str) -> str:
    # Check if emoji is a PartialEmoji
    if isinstance(emoji, PartialEmoji):
        # Return the emoji representation
        return str(emoji)  # or emoji.name if it's a custom emoji with a name

    if isinstance(emoji, str) and len(emoji) > 0:
        # Decode escape sequences if they exist
        try:
            if emoji.startswith("\\U") or emoji.startswith("\\u"):
                # Handle full Unicode escape sequences
                return emoji.encode("utf-8").decode("unicode_escape")
            else:
                # Return the emoji as is if it's already in raw form
                return emoji
        except Exception as e:
            print(f"Error normalizing emoji: {e}")
            return emoji  # Return original if something goes wrong

    return None  # If input is invalid