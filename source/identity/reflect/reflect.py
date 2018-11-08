
import asyncio
import fdk

async def handler(ctx, data=None, loop=None):
    """This function just reflects back the json that is supplied.
       This is useful for debugging clients that are calling this
       server
    """

    return data


if __name__ == "__main__":
    try:
        fdk.handle(handler)
    except Exception as e:
        print({"message": "Error! %s" % str(e), "status": -1})
    except:
        print({"message": "Unknown error!", "status": -1})

