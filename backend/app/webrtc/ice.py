import asyncio

from aiortc import RTCPeerConnection


async def wait_for_ice_gathering_complete(pc: RTCPeerConnection, timeout: float) -> None:
    if pc.iceGatheringState == "complete":
        return

    done = asyncio.Event()

    @pc.on("icegatheringstatechange")
    def on_change():
        if pc.iceGatheringState == "complete":
            done.set()

    try:
        await asyncio.wait_for(done.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        pass
