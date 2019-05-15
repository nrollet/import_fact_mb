import logging
import os
import sys
import pyodbc
import re
import random
import string
from datetime import datetime
from shutil import copyfile

def doc_rename(filename):
    """
    Outil pour renommer un document avec un nom aléatoire
    """
    salt = "".join(random.choice(string.ascii_lowercase) for _ in range(3))
    base = os.path.basename(filename)
    splitbase = base.split(".")
    base = splitbase[0] + "_" + salt + "." + splitbase[1]
    return base


class QuadraSetEnv(object):
    def __init__(self):

        self.cpta = ""
        self.paie = ""
        self.gi = ""
        self.conn = ""
        self.cur = ""
        self.clients = {}

    def read_ipl(self, ipl_file):
        """
        A partir du fichier IPL fournit en argument :
        - recupère les chemins pour accéder aux bases compta, paie et gi
        - génère la liste des clients sous la forme d'un dictionary
            - clé : code dossier
            - valeur : nom dossier
        """

        if not os.path.isfile(ipl_file):
            logging.error("{} introuvable".format(ipl_file))
            return False
        
        with open(ipl_file, "r") as f:
            lines = f.readlines()

        if len(lines)<2:
            logging.error("Ipl illisible")
            return False

        for line in lines:
            line = line.rstrip().replace("\\", "/")
            if "=" in line:
                key, item = line.split("=")[0:2]
                if key == "RACDATACPTA":
                    self.cpta = item
                elif key == "RACDATAPAIE":
                    self.paie = item
                elif key == "RACDATAGI":
                    self.gi = item

        #  Build list client 

        mdb_path = os.path.join(self.gi, "0000", "qgi.mdb")
        constr = "Driver={Microsoft Access Driver (*.mdb, *.accdb)};Dbq=" + mdb_path
        logging.info("openning qgi : {}".format(mdb_path))
        sql = """
            SELECT I.Code, I.Nom 
            FROM Intervenants I 
            INNER JOIN Clients C ON I.Code=C.Code 
            WHERE I.IsClient='1'
        """
        try:
            self.conn = pyodbc.connect(constr, autocommit=True)
            self.cur = self.conn.cursor()
            self.cur.execute(sql)
        except pyodbc.Error:
            logging.error(
                ("erreur requete base {} \n {}".format(mdb_path, sys.exc_info()[1]))
            )
        for item in list(self.cur):
            code, nom = item
            self.clients.update({code : nom})


    def make_db_path(self, num_dossier, type_dossier):
        """
        Génère chemin complet vers base access à partir
        du code dossier et type de base (DA, DS, DC)
        """
        type_dossier = type_dossier.upper()
        num_dossier = num_dossier.upper()
        db_path = ""
        if (
            type_dossier == "DC"
            or type_dossier.startswith("DA")
            or type_dossier.startswith("DS")
        ):
            db_path = "{}{}/{}/qcompta.mdb".format(self.cpta, type_dossier, num_dossier)

        elif type_dossier == "PAIE":
            db_path = "{}{}/qpaie.mdb".format(self.paie, num_dossier)

        return db_path
    
    def copy_to_images(self, num_dossier, type_dossier, filepath):
        """
        Méthode pour copier une nouvelle pièce comptable dans le
        dossier images 
        """
        filename = os.path.basename(filepath)
        img_path = os.path.join(self.cpta, type_dossier, num_dossier, "Images")
        # Si dossier Images absent
        if not os.path.isdir(img_path):
            os.mkdir(img_path)
        # Si un fichier porte le même nom
        if os.path.isfile(os.path.join(img_path, filename)):
            filename = doc_rename(filename)
        file_dest_path = os.path.join(img_path, filename)
        try:            
            copyfile(filepath, file_dest_path)
            logging.info("copie : {}".format(file_dest_path))
        except OSError as e:
            logging.error("Echec copie : {}".format(e))
            return False
        return True
        
    def dossier_annuel(self, num_dossier, type_dossier):
        """
        Si db dossier annuel présent (QDRaamm.mdb) dans le dossier
        on retourne le chemin complet
        """
        da_path = ""
        doss_cpta = os.path.join(self.cpta, type_dossier, num_dossier)
        for file in os.listdir(doss_cpta):
            file = file.upper()
            if re.match("^QDR[0-9]{4}\.MDB", file):
                da_path = os.path.join(doss_cpta, file)
                break
        return da_path

    def recent_situations(self, dossier):
        """
        Retrouver le chemin des dossiers de situation d'un client
        Pour des raisons de perf, on se contente de ne scanner 
        que n et n-1
        """
        situ_list = []

        annee = str(datetime.now().year)
        annee_1 = str(datetime.now().year - 1)
        for folder in os.listdir(self.cpta):
            folder = folder.upper()
            if (
                folder.startswith("DS"+annee) or
                folder.startswith("DS"+annee_1) 
            ):
                ds_path = os.path.join(self.cpta,folder)
                for subfold in os.listdir(ds_path):
                    if subfold == dossier:
                        situ_list.append(folder)
        return situ_list

    


if __name__ == "__main__":
    import pprint

    logging.basicConfig(
        level=logging.DEBUG, format="%(funcName)s\t\t%(levelname)s - %(message)s"
    )

    pp = pprint.PrettyPrinter(indent=4)
    # ipl = "C:/Users/nicolas/Documents/Pydio/mono.ipl"
    ipl = "C:/Users/nicolas/Documents/Pydio/mono.ipl"
    o = QuadraSetEnv()
    o.read_ipl(ipl)
    pp.pprint("---".join([o.cpta, o.paie, o.gi]))
    # pp.pprint(o.recent_situations("000868"))
    # pp.pprint(o.recent_situations("000063"))
    dossier = "000063"
    for item in o.recent_situations(dossier):
        print (o.make_db_path(dossier, item))
    print(o.dossier_annuel(dossier, "DC"))
    print(o.dossier_annuel("T00752", "DC"))
    print(doc_rename("toto.pdf"))
    
    # pp.pprint(o.clients)
    # print(o.make_db_path("FORM05", "DC"))
    # print(o.make_db_path("FORM05", "DA2017"))
    # print(o.make_db_path("form05", "PAIE"))
    # # print(o.gi_list_clients())
    # print(o.gi_list_clients())
