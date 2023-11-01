from tonpy.types.keys import Mnemonic, get_bip39_words, PrivateKey, PublicKey


def test_bip39():
    assert len(get_bip39_words()) == 2048


def test_mnemo():
    m = Mnemonic(words_count=48)
    words = m.get_words()
    key = m.get_private_key_hex()

    assert len(words) == 48
    assert len(key) == 64


def test_mnemo_2():
    mnemo = ['market', 'record', 'talent', 'wear', 'caught', 'soup', 'crater',
             'alpha', 'cattle', 'exercise', 'eight', 'page', 'easy', 'rural', 'tired', 'chapter',
             'major', 'make', 'organ', 'pipe', 'position', 'else', 'common', 'crop']
    m = Mnemonic(words=mnemo)
    assert m.get_private_key_hex() == '8A9184CC9D0A26F846BB85A1178425C0EB4BB5C489E8C8A9436960CCAF93C271'
    k = m.get_private_key()

    assert k.to_hex() == '8A9184CC9D0A26F846BB85A1178425C0EB4BB5C489E8C8A9436960CCAF93C271'
    assert k.get_public_key().to_hex() == ''


def test_private_key():
    key = PrivateKey()
    assert len(key.to_hex()) == 64


def test_private_key_v2():
    key = PrivateKey('8A9184CC9D0A26F846BB85A1178425C0EB4BB5C489E8C8A9436960CCAF93C271')
    assert key.to_hex() == '8A9184CC9D0A26F846BB85A1178425C0EB4BB5C489E8C8A9436960CCAF93C271'


def test_public_key():
    key = PrivateKey('8A9184CC9D0A26F846BB85A1178425C0EB4BB5C489E8C8A9436960CCAF93C271')
    assert key.get_public_key().to_hex() == '4895BC7F8E43E45C30E354F9DAD0FA08B8E5EB33D038BC130A0AF635B0080A5F'


def test_public_key_v2():
    key = PublicKey('4895BC7F8E43E45C30E354F9DAD0FA08B8E5EB33D038BC130A0AF635B0080A5F')
    assert key.to_hex() == '4895BC7F8E43E45C30E354F9DAD0FA08B8E5EB33D038BC130A0AF635B0080A5F'