# -*-coding:Utf-8 -*

import logging
import sys
import pyodbc
from datetime import datetime

class Compta_Connect():
    """
    Outils pour la manipuler la base Access Quadra
    """

    def __init__(self, qcompta_mdb):

        constr = 'Driver={Microsoft Access Driver (*.mdb, *.accdb)};Dbq='+ qcompta_mdb        

        try:
            logging.info("Connexion : {}".format(qcompta_mdb))
            self.conn = pyodbc.connect(constr, autocommit=True)
            self.cur = self.conn.cursor()       
        except pyodbc.Error :
            logging.error(("erreur requete base\n {}".format(sys.exc_info()[1])))


    def close_connection(self):
        self.conn.commit()
        self.conn.close()

    def verif_compte(self, compte):
        """
        Vérifie si compte présent dans le PC
        Return boolean
        """ 
        check = True     
        sSQL = (
            f"SELECT numero FROM Comptes "
            f"WHERE numero='{compte}'"
        )
        data = self.cur.execute(sSQL).fetchall()
        if not data:
            check = False
        return check

    def verif_journal(self, journal):
        """
        Vérifie si compte présent dans le PC
        Return boolean
        """ 
        check = True     
        sSQL = (
            f"SELECT Code FROM Journaux "
            f"WHERE code='{journal}'"
        )
        data = self.cur.execute(sSQL).fetchall()
        if not data:
            check = False
        return check        

    def verif_pieces(self, piece, fourn):
        """
        Vérifie si piece déjà présente dans la compta
        pour un fournisseur donné
        """
        check = True
        sSQL = ("SELECT NumeroPiece "
                "FROM Ecritures "
                f"WHERE NumeroCompte='{fourn}' "
                f"AND NumeroPiece='{piece}'"
        )        
        data = self.cur.execute(sSQL).fetchall()
        if not data:
            check = False
        return check  
    # def get_liste_pieces(self, compte_fourn):
    #     """
    #     Fournit la liste des numéros de pièces déjà présent
    #     Pour un fournisseur donné (numéro de compte)
    #     """

    #     lst_piece = []
    #     sSQL = ("SELECT DISTINCT(NumeroPiece) "
    #             "FROM Ecritures "
    #             "WHERE NumeroCompte='{}' "
    #             "ORDER BY NumeroPiece").format(compte_fourn)
        
    #     self.cur.execute(sSQL)
    #     for item in  list(self.cur):
    #         lst_piece.append(item[0])
    #     self.cur.close
    #     return lst_piece

    def get_last_uniq(self):
        """
        Retourne le dernier identifiant unique
        de la liste des écritures
        """

        sSQL = "SELECT MAX(NumUniq) FROM Ecritures"
        self.cur.execute(sSQL)
        self.cur.execute(sSQL)
        last_id = list(self.cur)[0][0]

        if last_id is None :
            last_id = 0        

        return last_id

    def get_last_lignefolio(self, journal, periode):
        """
        Retourne le dernier numero de ligne folio
        utilisé dans un journal
        """

        sSQL = ("SELECT MAX(LigneFolio) FROM Ecritures "
                "WHERE CodeJournal='{}' "
                "AND PeriodeEcriture=#{}#").format(journal, periode)

        self.cur.execute(sSQL)
        self.cur.execute(sSQL)
        last_lfolio = list(self.cur)[0][0]  

        if last_lfolio is None :
            last_lfolio = 0

        return last_lfolio

    def get_affectation_ana(self, compte):
        """
        Pour un compte donné, retourne le code analytique
        par défaut
        """

        sSQL = ("SELECT CodeCentre "
                "FROM AffectationAna "
                "WHERE Numcompte='{}'"
                .format(compte))
        
        self.cur.execute(sSQL)
        self.cur.execute(sSQL)
        data = list(self.cur)

        if data :
            affect = data[0][0]
        else:
            affect = ""

        return affect


    def _exec_sql(self, sql_string):
        """
        Execute la requete SQL passée en paramètre
        """

        try :
            self.cur.execute(sql_string)
        except pyodbc.Error :
            logging.error(("erreur requete base {}"
                                .format(sys.exc_info()[1])))
            exit()


    def maj_centralisateur(self, journal, periode, folio):
        """
        Pour la mise à jour du centralisateur après
        une injection d'écritures
        """

        sSQL_R = (
            # Comptes exploitation
            f"SELECT SUM(MontantTenuDebit), SUM(MontantTenuCredit) " 
            f"FROM Ecritures "
            f"WHERE CodeJournal='{journal}' "
            f"AND PeriodeEcriture=#{periode}# "
            f"AND Folio={folio} "
            f"AND TypeLigne='E' "
            f"AND NumeroCompte LIKE '[6-7]%' ")

        sSQL_F = (
            # Comptes Fournisseurs
            f"SELECT SUM(MontantTenuDebit), SUM(MontantTenuCredit) " 
            f"FROM Ecritures "
            f"WHERE CodeJournal='{journal}' "
            f"AND PeriodeEcriture=#{periode}# "
            f"AND Folio={folio} "
            f"AND TypeLigne='E' "
            f"AND NumeroCompte LIKE '0%' ")

        sSQL_C = (
            # Comptes Clients
            f"SELECT SUM(MontantTenuDebit), SUM(MontantTenuCredit) " 
            f"FROM Ecritures "
            f"WHERE CodeJournal='{journal}' "
            f"AND PeriodeEcriture=#{periode}# "
            f"AND Folio={folio} "
            f"AND TypeLigne='E' "
            f"AND NumeroCompte LIKE '9%' ")

        sSQL_B = (
            # Comptes bilan
            f"SELECT SUM(MontantTenuDebit), SUM(MontantTenuCredit) " 
            f"FROM Ecritures "
            f"WHERE CodeJournal='{journal}' "
            f"AND PeriodeEcriture=#{periode}# "
            f"AND Folio={folio} "
            f"AND TypeLigne='E' "
            f"AND NumeroCompte LIKE '[1-5]%' ")       

        sSQL_nbl = (
            # nbr lignes du folio
            f"SELECT COUNT(*) FROM Ecritures "
            f"WHERE CodeJournal='{journal}' "
            f"AND PeriodeEcriture=#{periode}# "
            f"AND Folio={folio} "
            f"AND TypeLigne='E' "
        ) 

        sSQL_nxt = (
            # nbr lignes du folio
            f"SELECT MAX(LigneFolio) + 10 FROM Ecritures "
            f"WHERE CodeJournal='{journal}' "
            f"AND PeriodeEcriture=#{periode}# "
            f"AND Folio={folio} "
            f"AND TypeLigne='E' "
        )           

        nb_lignes = self.cur.execute(sSQL_nbl).fetchall()[0][0]
        if not nb_lignes :
            nb_lignes = 0

        nxt_ligne = self.cur.execute(sSQL_nxt).fetchall()[0][0]
        if not nxt_ligne :
            nxt_ligne = 0

        deb_cli, cre_cli = self.cur.execute(sSQL_C).fetchall()[0]
        if not deb_cli:
            deb_cli = 0.0
        if not cre_cli:
            cre_cli = 0.0       

        deb_frn, cre_frn = self.cur.execute(sSQL_F).fetchall()[0]
        if not deb_frn:
            deb_frn = 0.0
        if not cre_frn:
            cre_frn = 0.0

        deb_bil, cre_bil = self.cur.execute(sSQL_B).fetchall()[0]
        if not deb_bil:
            deb_bil = 0.0
        if not cre_bil:
            cre_bil = 0.0

        deb_res, cre_res = self.cur.execute(sSQL_R).fetchall()[0]
        if not deb_res:
            deb_res = 0.0
        if not cre_res:
            cre_res = 0.0                                        

        sSQL_chk = (
            f"SELECT * FROM Centralisateur "
            f"WHERE CodeJournal='{journal}' "
            f"AND Periode=#{periode}# "
            f"AND Folio={folio} "
        )
        logging.debug(sSQL_chk)
        self.cur.execute(sSQL_chk)
        if list(self.cur):
            sSQL_upd = (
                f"UPDATE Centralisateur "
                f"SET NbLigneFolio={nb_lignes}, "
                f"ProchaineLigne={nxt_ligne}, "
                f"DebitClient={deb_cli}, "
                f"CreditClient={cre_cli}, "
                f"DebitFournisseur={deb_frn}, "
                f"CreditFournisseur={cre_frn}, "
                f"DebitClasse15={deb_bil}, "
                f"CreditClasse15={cre_bil}, "
                f"DebitClasse67={deb_res}, "
                f"CreditClasse67={cre_res} "
                f"WHERE "
                f"CodeJournal='{journal}' "
                f"AND Periode=#{periode}# "
                f"AND Folio={folio}")

        else:
            sSQL_upd = (
                "INSERT INTO Centralisateur "
                "(CodeJournal, Periode, Folio, "
                "NbLigneFolio, ProchaineLigne, "
                "DebitClient, CreditClient, "
                "DebitFournisseur, CreditFournisseur, "
                "DebitClasse15, CreditClasse15, "
                "DebitClasse67, CreditClasse67) "
                "VALUES "
                f"('{journal}', #{periode}#, {folio}, "
                f"{nb_lignes}, {nxt_ligne}, "
                f"{deb_cli}, {cre_cli}, "
                f"{deb_frn}, {cre_frn}, "
                f"{deb_bil}, {cre_bil}, "
                f"{deb_res}, {cre_res})"
            )
        logging.debug (sSQL_upd)

        self.cur.execute(sSQL_upd)

    def insert_ecrit(self, compte, journal, folio, date,
                     libelle, debit, credit, piece, image):

        """
        Insere une nouvelle ligne dans la table ecritures de Quadra.
        Ne vérifie pas si l'écriture est équilibrée au final.
        Ne passe pas de contrepartie.
        Si un code centre est passé dans les paramètres 
        une deuxième ligne de type A est ajoutée
        """

        Folio = "000"
        MontantSaisiDebit = 0
        MontantSaisiCredit = 0
        Quantite = 0
        NumLettrage = 0
        RapproBancaireOk = False
        NoLotEcritures = 0
        PieceInterne = 0
        CodeOperateur = "AUTO"
        Etat = 0
        NumLigne = 0
        TypeLigne = "E"
        Actif = False
        # NumEditLettrePaiement = 0
        PrctRepartition = 0
        ClientOuFrn = 0
        MontantAna = 0
        MilliemesAna = 0
        CodeTva = -1
        BonsAPayer = False
        MtDevForce = False
        EnLitige = False
        Quantite2 = 0
        NumEcrEco = 0
        NoLotFactor = 0
        Validee = False
        NoLotIs = 0
        NumMandat = 0
        DateSysSaisie = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        CompteContrepartie = ""   

        # Elements analytique invar.
        A_NumLigne = 1
        A_TypeLigne = "A"
        A_Nature = '*'
        A_PrctRepartition = 100
        A_TypeSaisie = 'P'  
        # A_Etat = 0      

        periode = datetime(date.year,
                           date.month,1)
        jour = date.day
      
        libelle = libelle[:30]
        piece = piece[0:10]

        uid = self.get_last_uniq() + 1
        lfolio = self.get_last_lignefolio(journal, periode) + 10

        centre = self.get_affectation_ana(compte)

        sSQL_G = (f"INSERT INTO Ecritures "
                "("
                    "NumUniq, "
                    "NumeroCompte, "
                    "CodeJournal, "
                    "Folio, "
                    "LigneFolio, "
                    "PeriodeEcriture, "
                    "JourEcriture, "
                    "Libelle, "
                    "MontantTenuDebit, "
                    "MontantTenuCredit, "
                    "MontantSaisiDebit, "
                    "MontantSaisiCredit, "
                    "CompteContrepartie, "
                    "Quantite, "
                    "NumeroPiece, "
                    "NumLettrage, "
                    "RapproBancaireOk, "
                    "NoLotEcritures, "
                    "PieceInterne, "
                    "CodeOperateur, "
                    "DateSysSaisie, "
                    "Etat, "
                    "NumLigne, "
                    "TypeLigne, "
                    "Actif, "
                    # "NumEditLettrePaiement, "
                    "PrctRepartition, "
                    "ClientOuFrn, "
                    "RefImage, "
                    "MontantAna, "
                    "MilliemesAna, "
                    "CentreSimple, "
                    "CodeTva, "
                    "BonsAPayer, "
                    "MtDevForce, "
                    "EnLitige, "
                    "Quantite2, "
                    "NumEcrEco, "
                    "NoLotFactor, "
                    "Validee, "
                    "NoLotIs, "
                    "NumMandat) "
                "VALUES "
                "("
                    f"{uid}, "
                    f"'{compte}', "
                    f"'{journal}', "
                    f"{folio}, "
                    f"{lfolio}, "
                    f"#{periode}#, "
                    f"{jour}, "
                    f"'{libelle}', "
                    f"{debit}, "
                    f"{credit}, "
                    f"{MontantSaisiDebit}, "
                    f"{MontantSaisiCredit}, "
                    f"'{CompteContrepartie}', "
                    f"{Quantite}, "
                    f"'{piece}', "
                    f"{NumLettrage}, "
                    f"{RapproBancaireOk}, "
                    f"{NoLotEcritures}, "
                    f"{PieceInterne}, "
                    f"'{CodeOperateur}', "
                    f"#{DateSysSaisie}#, "
                    f"{Etat}, "
                    f"{NumLigne}, "
                    f"'{TypeLigne}', "
                    f"{Actif}, "
                    # f"{NumEditLettrePaiement}, "
                    f"{PrctRepartition}, "
                    f"{ClientOuFrn}, "
                    f"'{image}', "
                    f"{MontantAna}, "
                    f"{MilliemesAna}, "
                    f"'{centre}', "
                    f"{CodeTva}, "
                    f"{BonsAPayer}, "
                    f"{MtDevForce}, "
                    f"{EnLitige}, "
                    f"{Quantite2}, "
                    f"{NumEcrEco}, "
                    f"{NoLotFactor}, "
                    f"{Validee}, "
                    f"{NoLotIs}, "
                    f"{NumMandat}) ") 
        # print (sSQL_G)
        self.cur.execute(sSQL_G)

        tab = (
            '|{:_>6}'.format(uid) + 
            '|{:_>2}'.format(TypeLigne) +
            '|{:_>4}'.format(lfolio) +
            '|{:_>7}'.format(periode.strftime("%d%m%y")) +
            '|{:_>3}'.format(jour) +
            '|{:_>9}'.format(compte) +
            '|{:_<22}'.format(libelle)[0:22] +
            '|{:_>8.2f}'.format(debit) +
            '|{:_>8.2f}'.format(credit) +
            '|{:_>8}'.format(piece)
        )
        logging.info(tab)

        if centre :
            montant = abs(debit - credit)
            uid += 1

            sSQL_A = (f"INSERT INTO Ecritures "
                    "("
                        "NumUniq, "
                        "NumeroCompte, "
                        "CodeJournal, "
                        "Folio, "
                        "LigneFolio, "
                        "PeriodeEcriture, "
                        "JourEcriture, "
                        "MontantTenuDebit, "
                        "MontantTenuCredit, "
                        "MontantSaisiDebit, "
                        "MontantSaisiCredit, "
                        "Quantite, "
                        "NumLettrage, "
                        "RapproBancaireOk, "
                        "NoLotEcritures, "
                        "PieceInterne, "
                        # "Etat, "
                        "NumLigne, "
                        "TypeLigne, "
                        "Actif, "
                        # "NumEditLettrePaiement, "
                        "Centre, "
                        "Nature, "
                        "PrctRepartition, "
                        "TypeSaisie, "
                        "MontantAna, "
                        "MilliemesAna, "
                        "CodeTva, "
                        "BonsAPayer, "
                        "MtDevForce, "
                        "EnLitige, "
                        "Quantite2, "
                        "NumEcrEco, "
                        "NoLotFactor, "
                        "Validee, "
                        "NoLotIs, "
                        "NumMandat) "
                    "VALUES "
                    "("
                        f"{uid}, "
                        f"'{compte}', "
                        f"'{journal}', "
                        f"{folio}, "
                        f"{lfolio}, "
                        f"#{periode}#, "
                        f"{jour}, "
                        f"{debit}, "
                        f"{credit}, "
                        f"{MontantSaisiDebit}, "
                        f"{MontantSaisiCredit}, "
                        f"{Quantite}, "
                        f"{NumLettrage}, "
                        f"{RapproBancaireOk}, "
                        f"{NoLotEcritures}, "
                        f"{PieceInterne}, "
                        # f"{A_Etat}, "
                        f"{A_NumLigne}, "
                        f"'{A_TypeLigne}', "
                        f"{Actif}, "
                        # f"{NumEditLettrePaiement}, "
                        f"'{centre}', "
                        f"'{A_Nature}', "
                        f"{A_PrctRepartition}, "
                        f"'{A_TypeSaisie}', "
                        f"{montant}, "
                        f"{MilliemesAna}, "
                        f"{CodeTva}, "
                        f"{BonsAPayer}, "
                        f"{MtDevForce}, "
                        f"{EnLitige}, "
                        f"{Quantite2}, "
                        f"{NumEcrEco}, "
                        f"{NoLotFactor}, "
                        f"{Validee}, "
                        f"{NoLotIs}, "
                        f"{NumMandat}) ")               
            # print (sSQL_A)
            self.cur.execute(sSQL_A)

            tab = (
                    '|{:_>6}'.format(uid) + 
                    '|{:_>2}'.format(A_TypeLigne) +
                    '|{:_>4}'.format(lfolio) +
                    '|'+'_'*7 +
                    '|'+'_'*3 +
                    '|'+'_'*9 +
                    '|{:_<4}{:_>17.2f}'.format(centre, montant) +
                    '|'+'_'*8 +
                    '|'+'_'*8 +
                    '|'+'_'*8
            )
            logging.info(tab)

        self.maj_centralisateur(journal, periode, folio)







if __name__ == '__main__':

    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    logging.basicConfig(level=logging.DEBUG,
                   format='%(module)s \t %(levelname)s -- %(message)s')

    cpta = "FORM05"
    periode = datetime(2018, 8, 1)
    conx = Compta_Connect(cpta)
    print(str(conx.get_last_uniq() + 1))
    # print(conx.get_affectation_ana('60110000'))
    # print(conx.get_affectation_ana('xxxxxxxx'))
    # print ("verif : " + str(conx.verif_compte("0ALF")))
    # conx.maj_centralisateur("MB", periode, 0)
    # conx.cur.execute (f"UPDATE Centralisateur SET NbLigneFolio=0, ProchaineLigne=0 "
    #                   f"WHERE CodeJournal='MB' AND Periode=#{periode}# AND Folio=0")
    # conx.cur.execute("SELECT * FROM Centralisateur WHERE CodeJournal='MB'")

    # # print (conx.cur.fetchall())
    # print(list(conx.cur))
    # if not conx.verif_pieces("nnn", "0MBR"):
    #     conx.insert_ecrit("62260000", "AC", 0, periode, "Facture MB 688676 du 21.08", 999.0, 0.0, "jjj", "")
    #     conx.insert_ecrit("0NEWTON", "AC", 0, periode, "gnok", 0, 999.0, "jjj", "")
    # else :
    #     logging.warning("nmumero de piece deja present!")

    # conx.cur.commit()
    conx.close_connection()