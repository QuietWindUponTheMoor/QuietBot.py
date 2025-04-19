from discord import File

async def CardFile(cardTuple: tuple, fileName="QuietBot_Card") -> File:
    """
    Takes in a card tuple and returns a file to be used in messages or interaction replies.

    :param: [cardTuple] (cardName, cardImagePath) The tuple retrieved of the card.
    :param: [fileName] The name of the png file that will be saved on Discord. (OPTIONAL)

    :returns: File to be used in messages or interaction replies
    :rtype: File
    """
    # Get the card name and file path
    cardName, path = cardTuple

    fileName = f"{fileName}.png".replace(" ", "_")
    return File(path, filename=fileName)