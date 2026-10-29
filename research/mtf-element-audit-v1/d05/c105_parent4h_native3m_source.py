"""C105 original Binance native3m provider ZIP + CSV SHA, frozen new 10 coins.
The C104 original provider checksum parser is used unchanged with a scoped local
allowlist override; original c104 source is neither edited nor stored modified.
"""
import c104_native3m_source as frozen
class C105SourceError(ValueError):pass
SYMBOLS=("BNBUSDT","XLMUSDT","HBARUSDT","INJUSDT","OPUSDT",
         "LDOUSDT","DOTUSDT","GALAUSDT","SANDUSDT","RUNEUSDT")
DAYS=frozen.DAYS
EXPECTED=320

def original_all(*,fetch=None):
    old=frozen.SYMBOLS
    try:
        frozen.SYMBOLS=SYMBOLS
        if fetch is None:return frozen.load()
        return frozen.load(fetch=fetch)
    finally:
        frozen.SYMBOLS=old
