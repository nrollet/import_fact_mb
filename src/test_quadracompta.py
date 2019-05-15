from quadracompta import Compta_Connect


def test_verif_compte():
    test_db = "src/tests/qcompta.mdb"
    Q = Compta_Connect(test_db)
    assert Q.verif_compte("51210000") == True
    Q.close_connection()

