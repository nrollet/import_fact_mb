import re
import os
import pprint
import logging
from datetime import datetime

class ParseurEdi(object):
    """
    Classe pour la gestion du fichier au format Edifact
    """
    def __init__ (self, file_path):
        """
        A l'instanciation, lecture du fichier edifact.
        Epurage.
        """

        with open(file_path, "r") as f:
            txt = f.readlines()
            # logging.info("parsing fichier edi : {}".format(file_path))

        self.rows = []
        self.dic = {"groups" : {}}

        for line in txt :
            self.rows.append(line.strip().replace("'", ""))       

    def read(self):
        """
        Récupère les données dont on a besoin. Numéro, date, ...
        et *tous* les articles (prix, qté, etc.). 
        Renvoi un dictionnaire.
        Voir plus bas dans les commentaires la structure 
        du dictionary
        """

        count = 0
        grp_id = ""

        for line in self.rows :

            # code du restaurant
            # RFF+IT:003296-001120'
            if re.match(r"^RFF\+IT:[0-9]*-[0-9]*", line):
                self.dic["resto"] = line.split(":")[1]
            
            # numero de la facture
            # type : facture (380), avoir (381)
            # BGM+380+815143+9'
            if re.match(r"^BGM\+38[0-1]\+[0-9]*\+9", line):
                self.dic["num"] = line.split("+")[2]
                self.dic["type"] = line.split("+")[1]
            
            # Date de la facture
            # DTM+137:20181107:102'
            elif re.match(r"^DTM\+137:[0-9]{8}:102", line): 
                extr = line.split(":")[1]
                date = datetime.strptime(extr, "%Y%m%d")         
                self.dic["date"] = date 
            
            # Catégorie d'article
            #   LIN+1++2:UP'
            # Quantité
            #   QTY+47:24:PCE'
            # Montant
            #   MOA+203:241.07'
            elif re.match(r"^LIN\+[0-9]*\+\+[0-9A-Z]*:UP", line):
                # Libelle du groupe sur la ligne + 1
                #   IMD+A+ANM+:::002 ALIMENTAIRE'
                grp_id = self.rows[count+1].split(":")[-1]
                self.dic["groups"].update({grp_id : {}})
                self.dic["groups"][grp_id].update({"items" : []})
                for sub_line in self.rows[count+1:]:
                    mark = sub_line.split("+")[0]
                    # Au prochain LIN ou UNS on break 
                    if (mark == "LIN" or mark == "UNS") :
                        break
                    elif mark == "QTY" :
                        grp_qty = sub_line.split("+")[1].split(":")[1]
                        self.dic["groups"][grp_id].update({"quantite" : grp_qty})
                    elif mark == "MOA":
                        grp_mnt = sub_line.split(":")[-1]
                        self.dic["groups"][grp_id].update({"montant" : float(grp_mnt)})                    

            # Détail des articles
            # code 
            #   PIA+5+134-915:SA::91'
            # libelle 
            #   IMD+A+ANM+:::SB MIX SALADE CROQUE COULEUR' 
            # quantite
            #   QTY+47:1:PCE'
            # montant 
            #   MOA+203:10.41'
            elif re.match(r"^LIN\+[0-9]*\+\+.*I", line) and grp_id:
                item_descr = ["", "", 0, 0.0]
                for sub_line in self.rows[count+1:]:
                    mark = sub_line.split("+")[0]                
                    if (mark == "LIN" or mark == "UNS") :
                        break
                    else:
                        if mark == "PIA": # code                  
                            item_descr[0] = sub_line.split("+")[2].split(":")[0] 
                        elif mark == "IMD": # libelle
                            item_descr[1] = sub_line.split(":")[-1] 
                        elif mark == "QTY": # quantite
                            item_descr[2] =  int(sub_line.split(":")[1]) 
                        elif mark == "MOA": # prix
                            item_descr[3] =  float(sub_line.split(":")[-1]) 
                        
                self.dic["groups"][grp_id]["items"].append(item_descr)
            
            elif line.startswith("UNS+S"):
                for sub_line in self.rows[count+1:]:
                        if sub_line.startswith("MOA+125:"):
                            totalht = sub_line.split(":")[-1]
                            self.dic.update({"totalht" : float(totalht)})
                        elif sub_line.startswith("MOA+128:"):
                            totalttc = sub_line.split(":")[-1]
                            self.dic.update({"totalttc" : float(totalttc)})
                        elif sub_line.startswith("MOA+124:"):
                            tva = sub_line.split(":")[-1]
                            self.dic.update({"TVA" : float(tva)})
                        elif sub_line.startswith("MOA+218:"):  
                            acompte = sub_line.split(":")[-1]
                            self.dic.update({"ACOMPTE" : float(acompte)})
                        elif sub_line.startswith("MOA+39:"):  
                            netap = sub_line.split(":")[-1]
                            self.dic.update({"netap" : float(netap)})
                        elif sub_line.startswith("TAX"):
                            break

            count += 1

        logging.debug(self.dic)
        
        return self.dic

#     def control(self):
#         result = {}
#         montant_total = 0.0
#         for group in self.dic["groups"] :
#             montant_group = 0.0
#             for code, lib, qty, price in self.dic["groups"][group]["items"]:
#                 montant_total += price
#                 montant_group += price

#             result.update({group : [round(montant_group, 2), 
#                                      self.dic["groups"][group]["montant"]]})

#             if round(montant_group, 2) == self.dic["groups"][group]["montant"]:
#                 logging.debug ("{:_<30}{:_>10} (OK)".format(group, round(montant_group, 2)))
#             else :
#                 logging.error ("{:_<30}{:_>10} ({})".format(group, 
#                                                      round(montant_group, 2),
#                                                      self.dic["groups"][group]["montant"]))
#                 result = 1
#         if round(montant_total, 2) == self.dic["totalht"]:
#             logging.debug ("{:_<30}{:_>10} (OK)".format("TOTAL.HT", round(montant_total, 2)))
#         else : 
#             logging.error ("{:_<30}{:_>10} ({})".format("TOTAL.HT", 
#                                                 round(montant_total, 2),
#                                                 self.dic["totalht"]))
#             result = 1
        
#         return result
 
# class MassEdi(object):
#     def check (self, folder):
#         lst = []
#         out_file = "masscheck.csv"
        
#         with open(out_file, "w") as f:
#             f.write("FACTURE;GROUPE;MNT.CALC;MNT.LU;DIFF;AVOIR\n")
#             for root, dir, files in os.walk(folder):
#                 for file in files :
#                     avoir = ""
#                     if file.endswith(".txt"):
#                         sublist = []
#                         file_path = os.path.join(root, file)   
#                         edi = ParseurEdi(file_path)
#                         data = edi.read()
#                         ctrl = edi.control()
#                         if data["type"] == "381" : 
#                             avoir = "X"
#                         for group in data["groups"]:
#                             val1, val2 = ctrl[group]
#                             diff = val1 - val2
#                             f.write(";".join([file, group, str(val1), str(val2), str(diff), avoir]))
#                             f.write("\n")
#                             if group == "009 ADMINSTR & STAT":
#                                 for w, x, y, z in data["groups"][group]["items"] :
#                                     f.write(";".join([file, x, "", "", "", avoir]))
#                                     f.write("\n")


# def ChercheAvoir(folder):
#     print ("liste des avoirs :")
#     for root, dir, files in os.walk(folder):
#         for file in files :
#             if file.endswith(".txt"):
#                 sublist = []
#                 file_path = os.path.join(root, file)   
#                 edi = ParseurEdi(file_path)
#                 datas = edi.read()
#                 if datas["type"] == "381" :
#                     print("\t{}".format(file))


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG,
                   format='%(module)s \t %(levelname)s -- %(message)s')
    import pprint
    pp = pprint.PrettyPrinter(indent=4)

    myObj = ParseurEdi("src/tests/113192.edi")
    pp.pprint(myObj.read())


    # obj = MassEdi()
    # obj.check("./newparse/full_test")

    # file_list = []

    # for root, dir, files in os.walk("./newparse/test"):
    #     for file in files :
    #         if file.endswith(".txt"):
    #             logging.info("")
    #             file_path = os.path.join(root, file)
    #             edi = ParseurEdi(file_path)
    #             dump = edi.read()
    #             pp.pprint(dump)

    #ChercheAvoir("./newparse/full_test")



    ## STRUCTURE DU DICTIONARY EDIFACT ##############################

    # {   'ACOMPTE': -1452.94,
    # 'TVA': 309.94,
    # 'date': datetime.datetime(2018, 9, 21, 0, 0),
    # 'groups': {   '001 SURGELE': {   'items': [   [   '12528-006',
    #                                                   'MUFFIN PEPITES CHOCO',
    #                                                   1,
    #                                                   13.26],
    #                                               ...
    #                                               [   '4430-085',
    #                                                   'POULET WRAP -MP',
    #                                                   2,
    #                                                   109.98]],
    #                                  'montant': 1585.89,
    #                                  'quantite': '94'},
    #               '002 ALIMENTAIRE': {   'items': [   [   '13215-000',
    #                                                       'BERLINGO POMME '
    #                                                       'PECHE SSA',
    #                                                       3,
    #                                                   ...
    #                                                   [   '3677-024',
    #                                                       'SAUCE FRITES 14ML 2',
    #                                                       4,
    #                                                       76.36]],
    #                                      'montant': 2704.7,
    #                                      'quantite': '95'},
    #               '003 EMBALLAGE': {   'items': [   [   '11580-079',
    #                                                     'SAC SALADE BAR',
    #                                                     6,
    #                                                     123.18],
    #                                                   ...
    #                                                 [   '163-656',
    #                                                     'BOITE MOY.FRITES /17',
    #                                                     1,
    #                                                     21.99]],
    #                                    'montant': 360.23,
    #                                    'quantite': '18'},
    #               '009 ADMINSTR & STAT': {   'items': [   [   '94700-006',
    #                                                           'DOLLIES '
    #                                                           'PLASTIQUES '
    #                                                           'RENDUES',
    #                                                           -1,
    #                                                           -19.82],
    #                                                       [   '94700-007',
    #                                                           'DOLLIES '
    #                                                           'PLASTIQUES '
    #                                                           'LIVREES',
    #                                                           4,
    #                                                           79.28],
    #                                                       [   '94700-012',
    #                                                           'DEMI PALETTES '
    #                                                           'RENDUES',
    #                                                           -14,
    #                                                           -126.7],
    #                                                       [   '94700-013',
    #                                                           'DEMI PALETTES '
    #                                                           'LIVREES',
    #                                                           7,
    #                                                           63.35]],
    #                                          'montant': -3.89,
    #                                          'quantite': '-4'}},
    # 'netap': 3503.93,
    # 'num': '737854',
    # 'resto': '003296-001120',
    # 'totalht': 4646.93,
    # 'totalttc': 4956.87,
    # 'type': '380'}