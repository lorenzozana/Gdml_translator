#! /usr/bin/env python

import os, sys, math, sqlite3

# Get the input lhe file
if len(sys.argv) < 2:
    print "\nYou must enter the FLUKA input file you wish to convert as the first arguement. Exiting \n"
    sys.exit(1)

try:    
    input_file = file( sys.argv[1], 'r')
    string_rot = file( sys.argv[1], 'r')
    material_list = file("material_list.txt", 'r')

except:
    print "\nThe entered file cannot be opened, please enter a vaild FLUKA input file. Exiting. \n"
    sys.exit(1)
    pass

if len(sys.argv) > 2:    
    output_file_name = sys.argv[2]
else:                    
    output_file_name = "output.gdml"

try:
    geometry_file_name = "geometry_"
    geometry_file_name += output_file_name
    geometry_file = file(geometry_file_name, "w")
    geometry_file.write("<solids> \n")
    position_file_name = "position_"
    position_file_name += output_file_name
    position_file = file(position_file_name, "w")
    position_file.write("<define>\n")
    position_file.write("<constant name=\"HALFPI\" value=\"pi/2.\"/> \n")
    position_file.write("<position name=\"center\" x=\"0\" y=\"0\" z=\"0\"/> \n")
    position_file.write("<rotation name=\"identity\" x=\"0\" y=\"0\" z=\"0\" /> \n")
    material_file_name = "material_"
    material_file_name += output_file_name
    material_file = file(material_file_name, "w")
    material_file.write("<materials> \n")

    
except:
    print "Cannot open output file named: " + output_file_name + "\nPlease enter a valid output file name as the 2nd arguement. Exiting"
    sys.exit(1)
    pass

print "Setup complete \nOpened file " + str(sys.argv[1]) + "  \nConverting to .root format and outputing to " + output_file_name

maxL = 100000
print " MAX LENGHT FOR PLANES SET TO" + str(maxL) + "cm \n"


# Create database connection to an in-memory database

connectionObject    = sqlite3.connect(":memory:")
# Obtain a cursor object
cursorObject        = connectionObject.cursor()
# Create a table in the in-memory database
createTable = "CREATE TABLE material(id int, Name varchar(32), Formula varchar(32), Z int, A real, Density real)"
cursorObject.execute(createTable)
#Create a table for the materials needed in the file
createTable = "CREATE TABLE material_infile(id int, Name varchar(32), Formula varchar(32), Z int, A real, Density real, towrite int)"
cursorObject.execute(createTable)
#Creating table for list of regions in order
createTable = "CREATE TABLE region_list(id int, Name varchar(32))"
cursorObject.execute(createTable)
# Print the tables 
# .tables command will not work as it is not SQL...hence querying the SQLite_master
cursorObject.execute("select * from SQLite_master where type=\"table\"")
print("Tables available in the in-memory database(main):")
tables = cursorObject.fetchall()
print("Listing tables from SQLite_master:")
for table in tables:

    print("------------------------------------------------------")

    print("DB Object Name: %s"%(table[0]))

    print("Name of the database object: %s"%(table[1]))

    print("Table Name: %s"%(table[2]))

    print("Root page: %s"%(table[3]))

    print("SQL statement: %s"%(table[4]))

    print("------------------------------------------------------")



mat_id = 1
mat_file_id = 1
for line in material_list:
    mat_name=line.split()[0]
    mat_form=line.split()[1]
    mat_Z=line.split()[2]
    mat_A=line.split()[3]
    mat_density=line.split()[4]
    # Insert material valus into the table

    insertValues = "INSERT INTO material values(" + str(mat_id) + ",\"" + str(mat_name) + "\",\"" + str(mat_form) + "\"," + str(mat_Z) + "," + str(mat_A) + "," + str(mat_density) + ")"

    cursorObject.execute(insertValues)
    mat_id += 1
    continue


#Now insert in the file and in the database some of the materials defined by default in FLUKA
#AIR
material_file.write("<material name=\"mat_AIR\">\n <D value=\".00122210\" />\n  <fraction n=\"0.0001248\" ref=\"el_CARBON\" />\n <fraction n=\"0.755267\" ref=\"el_NITROGEN\" />\n <fraction n=\"0.231781\" ref=\"el_OXYGEN\" />\n <fraction n=\"0.012827\" ref=\"el_ARGON\" />\n </material>")
#Add AIR to the material list already in the file to not be written and the elements to be written
insertValues = "INSERT INTO material_infile values(" + str(mat_file_id) + ",\"AIR\",\"\",\"\",\"\",\"\",0)"    
cursorObject.execute(insertValues)
mat_file_id +=1
mat_list_air = ['CARBON','NITROGEN','OXYGEN','ARGON']
for mat_name in mat_list_air:
    query_str = "SELECT * FROM material_infile where Name='" + str(mat_name) + "'"
    cursorObject.execute(query_str)
    record = cursorObject.fetchone()
    #if not present I look for it in the other database and add it.
    if record == None:
        query_str = "SELECT * FROM material where Name='" + str(mat_name) + "'"
        cursorObject.execute(query_str)
        record2 = cursorObject.fetchone()
        if record2 == None:
            print "!!!!!!!!!!! MATERIAL " + str(mat_name) + " NOT PRESENT IN THE DATABASE, PLEASE ADD"
        else:
            insertValues = "INSERT INTO material_infile values(" + str(mat_file_id) + ",\"" + record2[1] + "\",\"" + record2[2] + "\"," + str(record2[3]) + "," + str(record2[4]) + "," + str(record2[5]) + ",1)"
            cursorObject.execute(insertValues)
            mat_file_id +=1
    pass


#VACUUM
# I am assuming that the composition is like air, but the density is 1.608e-12*g/cm3 (same as air, but with pressure of 1e-6 torr). Chapter 8 https://hallaweb.jlab.org/github/halla-osp/version/Standard-Equipment-Manual.pdf  
material_file.write("<material name=\"mat_VACUUM\">\n <D value=\"1.608E-12\" />\n <fraction n=\"0.0001248\" ref=\"el_CARBON\" />\n <fraction n=\"0.755267\" ref=\"el_NITROGEN\" />\n <fraction n=\"0.231781\" ref=\"el_OXYGEN\" />\n <fraction n=\"0.012827\" ref=\"el_ARGON\" />\n </material>")
#Add VACUUM to the material list already in the file to not be written; the elements are the same as air
insertValues = "INSERT INTO material_infile values(" + str(mat_file_id) + ",\"VACUUM\",\"\",\"\",\"\",\"\",0)"    
cursorObject.execute(insertValues)
mat_file_id += 1


#BLACKHOLE
#Here I just need to define whatever material with density > 0.
#The material BLACKHOLE will neet to be hardcoded in the geant4 software, so that when this material is hit, the tracking is stopped. For now the material will be based on Argon, since I already have it defined before
material_file.write("<material name=\"mat_BLCKHOLE\">\n  <D value=\"1.0\" />\n <fraction n=\"1.0\" ref=\"el_ARGON\" />\n </material>")
#Add BLACKHOLE to the material list already in the file to not be written; the elements are the same as air
insertValues = "INSERT INTO material_infile values(" + str(mat_file_id) + ",\"BLCKHOLE\",\"\",\"\",\"\",\"\",0)"    
cursorObject.execute(insertValues)
mat_file_id += 1

print "!!!!!!! YOU MUST DEFINE THE MATERIAL WITH THE PROPERTY BLCKHOLE IN YOUR CODE !!!!!\n"



RPP_lenght=8
SPH_lenght=6
RCC_lenght=9
TRC_lenght=10
ELL_lenght=9
HALFPI=90

tra_dx = 0.0
tra_dy = 0.0
tra_dz = 0.0
rot_dx = 0.0
rot_dy = 0.0
rot_dz = 0.0

old_tra_dx = 0.0
old_tra_dy = 0.0
old_tra_dz = 0.0
old_rot_dx = 0.0
old_rot_dy = 0.0
old_rot_dz = 0.0


#Writing logicmother
geometry_file.write("<box name=\"BoxMother\"")
geometry_file.write(" x=\"")
geometry_file.write(str(5*maxL))
geometry_file.write("\" y=\"")
geometry_file.write(str(5*maxL))
geometry_file.write("\" z=\"")
geometry_file.write(str(5*maxL))
geometry_file.write("\" lunit=\"cm\"/>\n")




def import_material(line):
    global mat_file_id
    mat_Z = line[11:20].strip()
    if str(mat_Z) == "":
        mat_Z = 0.0
        pass
    mat_Density = line[31:40].strip()
    if str(mat_Density) == "":
        mat_Density = 0.0
        pass
    mat_A = line[61:70].strip()
    mat_A2 = line[21:30].strip()    
    if str(mat_A) == "":
        mat_A = 0.0
        pass
    if str(mat_A2) == "":
        mat_A2 = 0.0
        pass
    if float(mat_A2) > 0.0:
        mat_A = mat_A2
        pass
    mat_Z = float(mat_Z)
    mat_A = float(mat_A)
    mat_name = line[70:79].strip()
    query_str = "SELECT * FROM material_infile where Name='" + str(mat_name) + "' and towrite='1'"
    cursorObject.execute(query_str)
    record = cursorObject.fetchone()
    if record != None:
        print "Material " + str(mat_name) + " already written in the database"
        return
    material_file.write("<material name=\"mat_")
    material_file.write(mat_name)
    if mat_Z > 0.0:
        material_file.write("\" Z=\"")
        material_file.write(str(mat_Z))
    if mat_A > 0.0:
        material_file.write("\"> <D value=\"")
        material_file.write(str(mat_Density))
        material_file.write("\" /> <atom value=\"")
        material_file.write(str(mat_A))
    if mat_Z > 0.0 and mat_A == 0.0:
        #I need to get the value from the database. I am going to filter with mat_Z, since the name can be different
        query_str = "SELECT * FROM material where Z='" + str(mat_Z) + "'"
        cursorObject.execute(query_str)
        record = cursorObject.fetchone()
        mat_A = float(record[4])
        material_file.write("\"> <D value=\"")
        material_file.write(str(mat_Density))
        material_file.write("\" /> <atom value=\"")
        material_file.write(str(mat_A))
    if mat_Z > 0.0 or mat_A > 0.0:    
        material_file.write("\"/>")
    if mat_A == 0.0 and mat_Z == 0.0:
        material_file.write("\">")
        material_file.write(" <D value=\"")
        material_file.write(str(mat_Density))
        material_file.write("\" /> \n")
        i_mat = 0
        mat_amount = []
        mat_kind = []
        i=0
        for i in range(81):
            mat_amount.append(0.0)
            mat_kind.append(0.0)

        #I assume is a compound
        # I write it in the database not to be written.
        mat_form = ""
        insertValues = "INSERT INTO material_infile values(" + str(mat_file_id) + ",\"" + str(mat_name) + "\",\"" + str(mat_form) + "\"," + str(mat_Z) + "," + str(mat_A) + "," + str(mat_Density) + ",0)"    
        cursorObject.execute(insertValues)
        mat_file_id +=1
        for line_r in string_rot:
            if line_r.startswith("COMPOUND") and line_r[70:80].strip() == str(mat_name) :
                print "Found COMPOUND for material" + str(mat_name) + "\n"
                i = 0
                while i < 3:
                    if len(line_r[(11+i*20):(20+i*20)].strip()) > 0:
                        mat_amount[i_mat] = float(line_r[(11+i*20):(20+i*20)].strip())
                        mat_kind[i_mat] = line_r[(21+i*20):(30+i*20)].strip()
                        #Get info from database and put it in the used materials database
                        query_str = "SELECT * FROM material where Name='" + str(mat_kind[i_mat]) + "'"
                        cursorObject.execute(query_str)
                        record = cursorObject.fetchone()
                        query_str = "SELECT * FROM material_infile where Name='" + str(mat_kind[i_mat]) + "'"
                        cursorObject.execute(query_str)
                        record2 = cursorObject.fetchone()
                        #Now, I want to know if I have the material in the database and if I didn't write it already
                        if record != None and record2 == None:
                            insertValues = "INSERT INTO material_infile values(" + str(mat_file_id) + ",\"" + record[1] + "\",\"" + record[2] + "\"," + str(record[3]) + "," + str(record[4]) + "," + str(record[5]) + ",1 )"
                            cursorObject.execute(insertValues)
                            mat_file_id +=1
                        i_mat +=1
                    i += 1
            continue
        i=0
        while i < i_mat:

            if mat_amount[i] > 0.0:
                # by atoms
                material_file.write("<composite n=\"")
                material_file.write(str(int(mat_amount[i])))
                material_file.write("\" ref=\"el_")
                material_file.write(str(mat_kind[i]))
                material_file.write("\" /> \n")
            if mat_amount[i] < 0.0:
                # by mass part
                material_file.write("<fraction n=\"")
                material_file.write(str(-mat_amount[i]))
                material_file.write("\" ref=\"el_")
                material_file.write(str(mat_kind[i]))
                material_file.write("\" /> \n")
            i += 1
    string_rot.seek(0)
    pass

    material_file.write("</material> \n")
    if mat_A != 0.0 and mat_Z != 0.0:
        # I can write an element
        material_file.write("<element name=\"el_")
        material_file.write(mat_name)
        material_file.write("\" formula=\"\" Z=\"")
        material_file.write(str(mat_Z))
        material_file.write("\"> <atom value=\"")
        material_file.write(str(mat_A))
        material_file.write("\"/> </element> \n")
        # and put it in the database
        mat_form = ""
        insertValues = "INSERT INTO material_infile values(" + str(mat_file_id) + ",\"" + str(mat_name) + "\",\"" + str(mat_form) + "\"," + str(mat_Z) + "," + str(mat_A) + "," + str(mat_Density) + ",0)"    
        cursorObject.execute(insertValues)
        mat_file_id += 1
    pass

def import_assigma(line):
    global mat_file_id
    mat_name = line.split()[1]
    vol_name = line.split()[2]
    vol_name2 = line[31:40].strip()
    #Search the database if material is in file
    query_str = "SELECT * FROM material_infile where Name='" + str(mat_name) + "'"
    cursorObject.execute(query_str)
    record = cursorObject.fetchone()
    #if not present I look for it in the other database and add it.
    if record == None:
        query_str = "SELECT * FROM material where Name='" + str(mat_name) + "'"
        cursorObject.execute(query_str)
        record2 = cursorObject.fetchone()
        if record2 == None:
            print "!!!!!!!!!!! MATERIAL " + str(mat_name) + " NOT PRESENT IN THE DATABASE, PLEASE ADD"
        else:
            insertValues = "INSERT INTO material_infile values(" + str(mat_file_id) + ",\"" + record2[1] + "\",\"" + record2[2] + "\"," + str(record2[3]) + "," + str(record2[4]) + "," + str(record2[5]) + ",1)"
            cursorObject.execute(insertValues)
            mat_file_id +=1
    pass
    # Now connect the material to the volume NB: The volume is defined as name_0
    if str(vol_name2) == "":
        #in this case, just a single volume is assigned
        geometry_file.write("<volume name=\"vol_")
        geometry_file.write(vol_name)
        geometry_file.write("\"> \n  <materialref ref=\"mat_")
        geometry_file.write(mat_name)
        geometry_file.write("\"/> \n  <solidref ref=\"")
        geometry_file.write(vol_name)
        geometry_file.write("_0\"/> \n </volume> \n")
    else:
        #Now I have a list of volumes to be assigned to the same material
        #I need to get the list of volumes in this range
        #First I get the id in the database for each end of the range
        query_str = "SELECT * FROM region_list where Name='" + str(vol_name) + "'"
        cursorObject.execute(query_str)
        record = cursorObject.fetchone()
        reg1_id=0
        if record != None:
            #Region found in the list
            reg1_id = record[0]
        else:
            print "!?!!?!?!?!?! Region " + str(vol_name) + "not found in the list: CHECK YOUR CODE!!!!\n"
        #now get the id of the second volume
        query_str = "SELECT * FROM region_list where Name='" + str(vol_name2) + "'"
        cursorObject.execute(query_str)
        record = cursorObject.fetchone()
        reg2_id=0
        if record != None:
            #Region found in the list
            reg2_id = record[0]
        else:
            print "!?!!?!?!?!?! Region " + str(vol_name) + "not found in the list: CHECK YOUR CODE!!!!\n"
        #finally now select the regions between the two id found before.
        query_str = "SELECT * FROM region_list where id >='" + str(reg1_id) + "' and id <='" + str(reg2_id) + "'"
        cursorObject.execute(query_str)
        records = cursorObject.fetchall()
        for record in records:
            geometry_file.write("<volume name=\"vol_")
            geometry_file.write(str(record[1]))
            geometry_file.write("\"> \n  <materialref ref=\"mat_")
            geometry_file.write(mat_name)
            geometry_file.write("\"/> \n  <solidref ref=\"")
            geometry_file.write(str(record[1]))
            geometry_file.write("_0\"/> \n </volume> \n") 

        
        
def import_start_translat(line):
    global tra_dx, tra_dy, tra_dz
    global old_tra_dx, old_tra_dy, old_tra_dz
    
    old_tra_dx = tra_dx
    old_tra_dy = tra_dy
    old_tra_dz = tra_dz
    
    tra_dx = float(tra_dx) + float(line.split()[1])
    tra_dy = float(tra_dy) + float(line.split()[2])
    tra_dz = float(tra_dz) + float(line.split()[3])
    print "tra_dx = " + str(tra_dx) + "  tra_dy=" + str(tra_dy) + " tra_dz=" + str(tra_dz)

def import_end_translat(line):
    global tra_dx, tra_dy, tra_dz
    global old_tra_dx, old_tra_dy, old_tra_dz
    tra_dx = old_tra_dx
    tra_dy = old_tra_dy
    tra_dz = old_tra_dz
    print "tra_dx = " + str(tra_dx) + "  tra_dy=" + str(tra_dy) + " tra_dz=" + str(tra_dz)

def import_rot_defi(name):
    global string_rot
    global tra_dx, tra_dy, tra_dz
    global old_tra_dx, old_tra_dy, old_tra_dz
    global rot_dx, rot_dy, rot_dz
    global old_rot_dx, old_rot_dy, old_rot_dz
    old_tra_dx = tra_dx
    old_tra_dy = tra_dy
    old_tra_dz = tra_dz
    old_rot_dx = rot_dx
    old_rot_dy = rot_dy
    old_rot_dz = rot_dz

    for line_r in string_rot:
        if "ROT-DEF" in line_r and name in line_r:
            print "ROT-DEF found \n" + line_r
            axis= line_r[11:20].strip()
            theta= line_r[21:30].strip()
            phi= line_r[31:40].strip()
            if str(phi) == "":
                phi = 0.0
            pass
            tra_dx = line_r[41:50].strip()
            tra_dy = line_r[51:60].strip()
            tra_dz = line_r[61:70].strip()
            if str(tra_dx) == "":
                tra_dx = 0.0
            pass
            if str(tra_dy) == "":
                tra_dy = 0.0
            pass
            if str(tra_dz) == "":
                tra_dz = 0.0
            pass
            tra_dx = float(old_tra_dx) + float(tra_dx)
            tra_dy = float(old_tra_dy) + float(tra_dy)
            tra_dz = float(old_tra_dz) + float(tra_dz)
            print "tra_dx= " + str(tra_dx) + "  tra_dy=" + str(tra_dy) + " tra_dz=" + str(tra_dz)
            print "axis=" + str(axis) + "  phi=" + str(phi)
            if axis == "100.":
                #x axis
                print "phi=" + str(phi) + "\n"
                rot_dx= float(rot_dx) + float(phi)
            elif axis == "200.":
                #y axis
                print "phi=" + str(phi) + "\n"
                rot_dy= float(rot_dy) + float(phi)
            elif axis == "300.":
                #z axis
                print "phi=" + str(phi) + "\n"
                rot_dz= float(rot_dz) + float(phi)
            else :
                #z axis
                print "phi=" + str(phi) + "\n"
                rot_dz= float(rot_dz) + float(phi)
        pass
        continue

    print "tra_dx = " + str(tra_dx) + "  tra_dy=" + str(tra_dy) + " tra_dz=" + str(tra_dz)
    print "rot_dx = " + str(rot_dx) + "  rot_dy=" + str(rot_dy) + " rot_dz=" + str(rot_dz)
    string_rot.seek(0)


def import_end_rot_defi():
    global tra_dx, tra_dy, tra_dz
    global old_tra_dx, old_tra_dy, old_tra_dz
    global rot_dx, rot_dy, rot_dz
    global old_rot_dx, old_rot_dy, old_rot_dz
    tra_dx = old_tra_dx
    tra_dy = old_tra_dy
    tra_dz = old_tra_dz
    rot_dx = old_rot_dx
    rot_dy = old_rot_dy
    rot_dz = old_rot_dz
    print "tra_dx = " + str(tra_dx) + "  tra_dy=" + str(tra_dy) + " tra_dz=" + str(tra_dz)


def importRPP(line):
    RPP_lenght = 8
    RPP_this = int(len(line.split()))
    name = line.split()[1]
    geometry_file.write("<box name=\"")
    geometry_file.write(name)
    xmin = float(line.split()[2])
    xmax = float(line.split()[3])
    geometry_file.write("\" x=\"")
    geometry_file.write(str(xmax-xmin))
    ymin = float(line.split()[4])
    ymax = float(line.split()[5])
    geometry_file.write("\" y=\"")
    geometry_file.write(str(ymax-ymin))
    zmin = float(line.split()[6])
    zmax = float(line.split()[7])
    geometry_file.write("\" z=\"")
    geometry_file.write(str(zmax-zmin))
    geometry_file.write("\" lunit=\"cm\"/>\n")
    
    position_file.write("<position name=\"pos_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(0.5*xmax+0.5*xmin+tra_dx))
    position_file.write("\" y=\"")
    position_file.write(str(0.5*ymax+0.5*ymin+tra_dy))
    position_file.write("\" z=\"")
    position_file.write(str(0.5*zmax+0.5*zmin+tra_dz))
    position_file.write("\" /> \n")
    position_file.write("<rotation name=\"rot_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(rot_dx))
    position_file.write("\" y=\"")
    position_file.write(str(rot_dy))
    position_file.write("\" z=\"")
    position_file.write(str(rot_dz))
    position_file.write("\" unit=\"deg\"/> \n")


def importRPPlong(line1,line2):
    RPP_lenght = 8
    value = []
    for i in range(10):
        value.append(i)

    RPP_this = int(len(line1.split()))
    for x in range(RPP_this):
        value[int(x)] = line1.split()[int(x)]
    for x in range(len(line2.split())):
            value[int(RPP_this + x)]= line2.split()[int(x)]
    name = value[1]
    geometry_file.write("<box name=\"")
    geometry_file.write(name)
    xmin = float(value[2])
    xmax = float(value[3])
    geometry_file.write("\" x=\"")
    geometry_file.write(str(xmax-xmin))
    ymin = float(value[4])
    ymax = float(value[5])
    geometry_file.write("\" y=\"")
    geometry_file.write(str(ymax-ymin))
    zmin = float(value[6])
    zmax = float(value[7])
    geometry_file.write("\" z=\"")
    geometry_file.write(str(zmax-zmin))
    geometry_file.write("\" lunit=\"cm\"/>\n")

    position_file.write("<position name=\"pos_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(0.5*xmax+0.5*xmin+tra_dx))
    position_file.write("\" y=\"")
    position_file.write(str(0.5*ymax+0.5*ymin+tra_dy))
    position_file.write("\" z=\"")
    position_file.write(str(0.5*zmax+0.5*zmin+tra_dz))
    position_file.write("\" /> \n")
    position_file.write("<rotation name=\"rot_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(rot_dx))
    position_file.write("\" y=\"")
    position_file.write(str(rot_dy))
    position_file.write("\" z=\"")
    position_file.write(str(rot_dz))
    position_file.write("\" unit=\"deg\"/> \n")


def importSPH(line):
    name = line.split()[1]
    geometry_file.write("<sphere name=\"")
    geometry_file.write(name)
    geometry_file.write("\" rmin=\"0\"")
    rmax = float(line.split()[5])
    geometry_file.write(" rmax=\"")
    geometry_file.write(str(rmax))
    geometry_file.write("\" deltatheta=\"180\"  deltaphi=\"360\" aunit=\"deg\" lunit=\"cm\"/>\n")
    xval = float(line.split()[2])
    yval = float(line.split()[3])
    zval = float(line.split()[4])

    position_file.write("<position name=\"pos_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(xval+tra_dx))
    position_file.write("\" y=\"")
    position_file.write(str(yval+tra_dy))
    position_file.write("\" z=\"")
    position_file.write(str(zval+tra_dz))
    position_file.write("\" /> \n")
    position_file.write("<rotation name=\"rot_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(rot_dx))
    position_file.write("\" y=\"")
    position_file.write(str(rot_dy))
    position_file.write("\" z=\"")
    position_file.write(str(rot_dz))
    position_file.write("\" unit=\"deg\"/> \n")

def importRCC(line):
    RCC_lenght = 9
    RCC_this = int(len(line.split()))
    name = line.split()[1]
    rmax = float(line.split()[8])
    xval = float(line.split()[2])
    yval = float(line.split()[3])
    zval = float(line.split()[4])
    hxval = float(line.split()[5])
    hyval = float(line.split()[6])
    hzval = float(line.split()[7])
    geometry_file.write("<tube name=\"")
    geometry_file.write(name)
    geometry_file.write("\" rmin=\"0.0\" rmax=\"")
    geometry_file.write(str(rmax))
    if hzval != 0.0 and hxval==0.0 and hyval==0.0:
        geometry_file.write("\" z=\"")
        geometry_file.write(str(abs(hzval)))
        geometry_file.write("\"  deltaphi=\"360\"  startphi=\"0.0\"  aunit=\"deg\"  lunit=\"cm\"/> \n")
        position_file.write("<position name=\"pos_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(xval+tra_dx))
        position_file.write("\" y=\"")
        position_file.write(str(yval+tra_dy))
        position_file.write("\" z=\"")
        position_file.write(str(zval+0.5*hzval+tra_dz))
        position_file.write("\" /> \n")
        position_file.write("<rotation name=\"rot_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(rot_dx))
        position_file.write("\" y=\"")
        position_file.write(str(rot_dy))
        position_file.write("\" z=\"")
        position_file.write(str(rot_dz))
        position_file.write("\" unit=\"deg\"/> \n")

    elif hxval != 0.0 and hzval==0.0 and hyval==0.0:
        geometry_file.write("\" z=\"")
        geometry_file.write(str(abs(hxval)))
        geometry_file.write("\"  deltaphi=\"360\"  startphi=\"0.0\"  aunit=\"deg\"  lunit=\"cm\"/> \n")
        position_file.write("<position name=\"pos_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(xval+0.5*hxval+tra_dx))
        position_file.write("\" y=\"")
        position_file.write(str(yval+tra_dy))
        position_file.write("\" z=\"")
        position_file.write(str(zval+tra_dz))
        position_file.write("\" /> \n")
        position_file.write("<rotation name=\"rot_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(rot_dx))
        position_file.write("\" y=\"")
        position_file.write(str(rot_dy+HALFPI))
        position_file.write("\" z=\"")
        position_file.write(str(rot_dz))
        position_file.write("\" unit=\"deg\"/> \n")
    elif hyval != 0.0 and hzval==0.0 and hxval==0.0:
        geometry_file.write("\" z=\"")
        geometry_file.write(str(abs(hyval)))
        geometry_file.write("\"  deltaphi=\"360\"  startphi=\"0.0\"  aunit=\"deg\"  lunit=\"cm\"/> \n")
        position_file.write("<position name=\"pos_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(xval+tra_dx))
        position_file.write("\" y=\"")
        position_file.write(str(yval+0.5*hyval+tra_dy))
        position_file.write("\" z=\"")
        position_file.write(str(zval+tra_dz))
        position_file.write("\" /> \n")
        position_file.write("<rotation name=\"rot_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(rot_dx+HALFPI))
        position_file.write("\" y=\"")
        position_file.write(str(rot_dy))
        position_file.write("\" z=\"")
        position_file.write(str(rot_dz))
        position_file.write("\" unit=\"deg\"/> \n")
    else:
        print("SORRY, RCC not in an axis dimension not yet implemented")
    pass



def importRCClong(line1,line2):
    RCC_lenght = 9
    value = []
    for i in range(10):
        value.append(i)

    RCC_this = int(len(line1.split()))
    for x in range(RCC_this):
        value[int(x)] = line1.split()[int(x)]
    for x in range(len(line2.split())):
            value[int(RCC_this + x)]= line2.split()[int(x)]
    name = value[1]
    rmax = float(value[8])
    xval = float(value[2])
    yval = float(value[3])
    zval = float(value[4])
    hxval = float(value[5])
    hyval = float(value[6])
    hzval = float(value[7])

    geometry_file.write("<tube name=\"")
    geometry_file.write(name)
    geometry_file.write("\"rmin=\"0.0\" rmax=\"")
    geometry_file.write(str(rmax))
    if hzval != 0.0 and hxval==0.0 and hyval==0.0:
        geometry_file.write("\" z=\"")
        geometry_file.write(str(abs(hzval)))
        geometry_file.write("\"  deltaphi=\"360\"  startphi=\"0.0\"  aunit=\"deg\"  lunit=\"cm\"/> \n")
        position_file.write("<position name=\"pos_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(xval+tra_dx))
        position_file.write("\" y=\"")
        position_file.write(str(yval+tra_dy))
        position_file.write("\" z=\"")
        position_file.write(str(zval+0.5*hzval+tra_dz))
        position_file.write("\" /> \n")
        position_file.write("<rotation name=\"rot_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(rot_dx))
        position_file.write("\" y=\"")
        position_file.write(str(rot_dy))
        position_file.write("\" z=\"")
        position_file.write(str(rot_dz))
        position_file.write("\" unit=\"deg\"/> \n")
    elif hxval != 0.0 and hzval==0.0 and hyval==0.0:
        geometry_file.write("\" z=\"")
        geometry_file.write(str(abs(hxval)))
        geometry_file.write("\"  deltaphi=\"360\"  startphi=\"0.0\"  aunit=\"deg\"  lunit=\"cm\"/> \n")
        position_file.write("<position name=\"pos_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(xval+0.5*hxval+tra_dx))
        position_file.write("\" y=\"")
        position_file.write(str(yval+tra_dy))
        position_file.write("\" z=\"")
        position_file.write(str(zval+tra_dz))
        position_file.write("\" /> \n")
        position_file.write("<rotation name=\"rot_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(rot_dx))
        position_file.write("\" y=\"")
        position_file.write(str(rot_dy+HALFPI))
        position_file.write("\" z=\"")
        position_file.write(str(rot_dz))
        position_file.write("\" unit=\"deg\"/> \n")
    elif hyval != 0.0 and hzval==0.0 and hxval==0.0:
        geometry_file.write("\" z=\"")
        geometry_file.write(str(abs(hyval)))
        geometry_file.write("\"  deltaphi=\"360\"  startphi=\"0.0\"  aunit=\"deg\"  lunit=\"cm\"/> \n")
        position_file.write("<position name=\"pos_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(xval+tra_dx))
        position_file.write("\" y=\"")
        position_file.write(str(yval+0.5*hyval+tra_dy))
        position_file.write("\" z=\"")
        position_file.write(str(zval+tra_dz))
        position_file.write("\" /> \n")
        position_file.write("<rotation name=\"rot_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(rot_dx+HALFPI))
        position_file.write("\" y=\"")
        position_file.write(str(rot_dy))
        position_file.write("\" z=\"")
        position_file.write(str(rot_dz))
        position_file.write("\" unit=\"deg\"/> \n")
    else:
        print("SORRY, !!!!!!RCC not in an axis dimension not yet implemented!!!!!!!!!")
    pass   

def importTRC(line):
    TRC_lenght = 10
    TRC_this = int(len(line.split()))
    name = line.split()[1]
    rmax1 = float(line.split()[8])
    rmax2 = float(line.split()[9])
    xval = float(line.split()[2])
    yval = float(line.split()[3])
    zval = float(line.split()[4])
    hxval = float(line.split()[5])
    hyval = float(line.split()[6])
    hzval = float(line.split()[7])
    geometry_file.write("<cone name=\"")
    geometry_file.write(name)
    geometry_file.write("\" rmin1=\"0.0\" rmax1=\"")
    geometry_file.write(str(rmax1))
    geometry_file.write("\" rmin2=\"0.0\" rmax2=\"")
    geometry_file.write(str(rmax2))
    if hzval != 0.0 and hxval==0.0 and hyval==0.0:
        geometry_file.write("\" z=\"")
        geometry_file.write(str(abs(hzval)))
        geometry_file.write("\"  deltaphi=\"360\"  startphi=\"0.0\"  aunit=\"deg\"  lunit=\"cm\"/> \n")
        position_file.write("<position name=\"pos_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(xval+tra_dx))
        position_file.write("\" y=\"")
        position_file.write(str(yval+tra_dy))
        position_file.write("\" z=\"")
        position_file.write(str(zval+0.5*hzval+tra_dz))
        position_file.write("\" /> \n")
        position_file.write("<rotation name=\"rot_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(rot_dx))
        position_file.write("\" y=\"")
        position_file.write(str(rot_dy))
        position_file.write("\" z=\"")
        position_file.write(str(rot_dz))
        position_file.write("\" unit=\"deg\"/> \n")
    elif hxval != 0.0 and hzval==0.0 and hyval==0.0:
        geometry_file.write("\" z=\"")
        geometry_file.write(str(abs(hxval)))
        geometry_file.write("\"  deltaphi=\"360\"  startphi=\"0.0\"  aunit=\"deg\"  lunit=\"cm\"/> \n")
        position_file.write("<position name=\"pos_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(xval+0.5*hxval+tra_dx))
        position_file.write("\" y=\"")
        position_file.write(str(yval+tra_dy))
        position_file.write("\" z=\"")
        position_file.write(str(zval+tra_dz))
        position_file.write("\" /> \n")
        position_file.write("<rotation name=\"rot_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(rot_dx))
        position_file.write("\" y=\"")
        position_file.write(str(rot_dy+HALFPI))
        position_file.write("\" z=\"")
        position_file.write(str(rot_dz))
        position_file.write("\" unit=\"deg\"/> \n")
    elif hyval != 0.0 and hzval==0.0 and hxval==0.0:
        geometry_file.write("\" z=\"")
        geometry_file.write(str(abs(hyval)))
        geometry_file.write("\"  deltaphi=\"360\"  startphi=\"0.0\"  aunit=\"deg\"  lunit=\"cm\"/> \n")
        position_file.write("<position name=\"pos_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(xval+tra_dx))
        position_file.write("\" y=\"")
        position_file.write(str(yval+0.5*hyval+tra_dy))
        position_file.write("\" z=\"")
        position_file.write(str(zval+tra_dz))
        position_file.write("\" /> \n")
        position_file.write("<rotation name=\"rot_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(rot_dx+HALFPI))
        position_file.write("\" y=\"")
        position_file.write(str(rot_dy))
        position_file.write("\" z=\"")
        position_file.write(str(rot_dz))
        position_file.write("\" unit=\"deg\"/> \n")
    else:
        print("SORRY, TRC not in an axis dimension not yet implemented")
    pass



def importTRClong(line1,line2):
    TRC_lenght = 10
    value = []
    for i in range(11):
        value.append(i)

    TRC_this = int(len(line1.split()))
    for x in range(TRC_this):
        value[int(x)] = line1.split()[int(x)]
    for x in range(len(line2.split())):
            value[int(TRC_this + x)]= line2.split()[int(x)]
    name = value[1]
    rmax1 = float(value[8])
    rmax2 = float(value[9])
    xval = float(value[2])
    yval = float(value[3])
    zval = float(value[4])
    hxval = float(value[5])
    hyval = float(value[6])
    hzval = float(value[7])

    geometry_file.write("<cone name=\"")
    geometry_file.write(name)
    geometry_file.write("\" rmin1=\"0.0\" rmax1=\"")
    geometry_file.write(str(rmax1))
    geometry_file.write("\" rmin2=\"0.0\" rmax2=\"")
    geometry_file.write(str(rmax2))
    if hzval != 0.0 and hxval==0.0 and hyval==0.0:
        geometry_file.write("\" z=\"")
        geometry_file.write(str(abs(hzval)))
        geometry_file.write("\"  deltaphi=\"360\"  startphi=\"0.0\"  aunit=\"deg\"  lunit=\"cm\"/> \n")
        position_file.write("<position name=\"pos_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(xval+tra_dx))
        position_file.write("\" y=\"")
        position_file.write(str(yval+tra_dy))
        position_file.write("\" z=\"")
        position_file.write(str(zval+0.5*hzval+tra_dz))
        position_file.write("\" /> \n")
        position_file.write("<rotation name=\"rot_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(rot_dx))
        position_file.write("\" y=\"")
        position_file.write(str(rot_dy))
        position_file.write("\" z=\"")
        position_file.write(str(rot_dz))
        position_file.write("\" unit=\"deg\"/> \n")
    elif hxval != 0.0 and hzval==0.0 and hyval==0.0:
        geometry_file.write("\" z=\"")
        geometry_file.write(str(abs(hxval)))
        geometry_file.write("\"  deltaphi=\"360\"  startphi=\"0.0\"  aunit=\"deg\"  lunit=\"cm\"/> \n")
        position_file.write("<position name=\"pos_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(xval+0.5*hxval+tra_dx))
        position_file.write("\" y=\"")
        position_file.write(str(yval+tra_dy))
        position_file.write("\" z=\"")
        position_file.write(str(zval+tra_dz))
        position_file.write("\" /> \n")
        position_file.write("<rotation name=\"rot_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(rot_dx))
        position_file.write("\" y=\"")
        position_file.write(str(rot_dy+HALFPI))
        position_file.write("\" z=\"")
        position_file.write(str(rot_dz))
        position_file.write("\" unit=\"deg\"/> \n")
    elif hyval != 0.0 and hzval==0.0 and hxval==0.0:
        geometry_file.write("\" z=\"")
        geometry_file.write(str(abs(hyval)))
        geometry_file.write("\"  deltaphi=\"360\"  startphi=\"0.0\"  aunit=\"deg\"  lunit=\"cm\"/> \n")
        position_file.write("<position name=\"pos_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(xval+tra_dx))
        position_file.write("\" y=\"")
        position_file.write(str(yval+0.5*hyval+tra_dy))
        position_file.write("\" z=\"")
        position_file.write(str(zval+tra_dz))
        position_file.write("\" /> \n")
        position_file.write("<rotation name=\"rot_");
        position_file.write(name);
        position_file.write("\" x=\"")
        position_file.write(str(rot_dx+HALFPI))
        position_file.write("\" y=\"")
        position_file.write(str(rot_dy))
        position_file.write("\" z=\"")
        position_file.write(str(rot_dz))
        position_file.write("\" unit=\"deg\"/> \n")
    else:
        print("SORRY, !!!!!!TRC not in an axis dimension not yet implemented!!!!!!!!!")
    pass   



def importELL(line):
    ELL_lenght = 9
    ELL_this = int(len(line.split()))
    name = line.split()[1]
    fx1 = float(line.split()[2])
    fy1 = float(line.split()[3])
    fz1 = float(line.split()[4])
    fx2 = float(line.split()[5])
    fy2 = float(line.split()[6])
    fz2 = float(line.split()[7])
    ellL = float(line.split()[8])
    val_a = ellL/2
    val_b = val_a**2 - 4 * ( (fx1-fx2)**2+(fy1-fy2)**2+(fz1-fz2)**2)
    geometry_file.write("<ellipsoid name=\"")
    geometry_file.write(name)
    position_file.write("<position name=\"pos_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(0.5*fx1+0.5*fx2+tra_dx))
    position_file.write("\" y=\"")
    position_file.write(str(0.5*fy1+0.5*fy2+tra_dy))
    position_file.write("\" z=\"")
    position_file.write(str(0.5*fz1+0.5*fz2+tra_dz))
    position_file.write("\" /> \n")
    position_file.write("<rotation name=\"rot_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(rot_dx))
    position_file.write("\" y=\"")
    position_file.write(str(rot_dy))
    position_file.write("\" z=\"")
    position_file.write(str(rot_dz))
    position_file.write("\" unit=\"deg\"/> \n")

    if (fz2-fz1) != 0.0 and (fx2-fx1)==0.0 and (fy2-fy1)==0.0:
        geometry_file.write("\" ax=\"")
        geometry_file.write(str(val_b))
        geometry_file.write("\" ay=\"")
        geometry_file.write(str(val_b))
        geometry_file.write("\" az=\"")
        geometry_file.write(str(val_a))
        geometry_file.write("\" lunit=\"cm\"/> \n")
    elif (fz2-fz1) == 0.0 and (fx2-fx1)!=0.0 and (fy2-fy1)==0.0:
        geometry_file.write("\" ax=\"")
        geometry_file.write(str(val_a))
        geometry_file.write("\" ay=\"")
        geometry_file.write(str(val_b))
        geometry_file.write("\" az=\"")
        geometry_file.write(str(val_b))
        geometry_file.write("\" lunit=\"cm\"/> \n")
    elif (fz2-fz1) == 0.0 and (fx2-fx1)==0.0 and (fy2-fy1)!=0.0:
        geometry_file.write("\" ax=\"")
        geometry_file.write(str(val_b))
        geometry_file.write("\" ay=\"")
        geometry_file.write(str(val_a))
        geometry_file.write("\" az=\"")
        geometry_file.write(str(val_b))
        geometry_file.write("\" lunit=\"cm\"/> \n")
    else:
        print("SORRY, ELL not in an axis dimension not yet implemented")
    pass



def importELLlong(line1,line2):
    ELL_lenght = 9
    value = []
    for i in range(11):
        value.append(i)

    ELL_this = int(len(line1.split()))
    for x in range(ELL_this):
        value[int(x)] = line1.split()[int(x)]
    for x in range(len(line2.split())):
            value[int(ELL_this + x)]= line2.split()[int(x)]
    name = value[1]
    fx1 = float(value[2])
    fy1 = float(value[3])
    fz1 = float(value[4])
    fx2 = float(value[5])
    fy2 = float(value[6])
    fz2 = float(value[7])
    ellL = float(value[8])
    val_a = ellL/2
    val_b = val_a**2 - 4 * ( (fx1-fx2)**2+(fy1-fy2)**2+(fz1-fz2)**2)
    geometry_file.write("<ellipsoid name=\"")
    geometry_file.write(name)
    position_file.write("<position name=\"pos_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(0.5*fx1+0.5*fx2+tra_dx))
    position_file.write("\" y=\"")
    position_file.write(str(0.5*fy1+0.5*fy2+tra_dy))
    position_file.write("\" z=\"")
    position_file.write(str(0.5*fz1+0.5*fz2+tra_dz))
    position_file.write("\" /> \n")
    position_file.write("<rotation name=\"rot_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(rot_dx))
    position_file.write("\" y=\"")
    position_file.write(str(rot_dy))
    position_file.write("\" z=\"")
    position_file.write(str(rot_dz))
    position_file.write("\" unit=\"deg\"/> \n")

    if (fz2-fz1) != 0.0 and (fx2-fx1)==0.0 and (fy2-fy1)==0.0:
        geometry_file.write("\" ax=\"")
        geometry_file.write(str(val_b))
        geometry_file.write("\" ay=\"")
        geometry_file.write(str(val_b))
        geometry_file.write("\" az=\"")
        geometry_file.write(str(val_a))
        geometry_file.write("\" lunit=\"cm\"/> \n")
    elif (fz2-fz1) == 0.0 and (fx2-fx1)!=0.0 and (fy2-fy1)==0.0:
        geometry_file.write("\" ax=\"")
        geometry_file.write(str(val_a))
        geometry_file.write("\" ay=\"")
        geometry_file.write(str(val_b))
        geometry_file.write("\" az=\"")
        geometry_file.write(str(val_b))
        geometry_file.write("\" lunit=\"cm\"/> \n")
    elif (fz2-fz1) == 0.0 and (fx2-fx1)==0.0 and (fy2-fy1)!=0.0:
        geometry_file.write("\" ax=\"")
        geometry_file.write(str(val_b))
        geometry_file.write("\" ay=\"")
        geometry_file.write(str(val_a))
        geometry_file.write("\" az=\"")
        geometry_file.write(str(val_b))
        geometry_file.write("\" lunit=\"cm\"/> \n")
    else:
        print("SORRY, ELL not in an axis dimension not yet implemented")
    pass

def importXYP(line):
    name = line.split()[1]
    geometry_file.write("<box name=\"")
    geometry_file.write(name)
    geometry_file.write("\" x=\"")
    geometry_file.write(str(maxL))
    geometry_file.write("\" y=\"")
    geometry_file.write(str(maxL))
    geometry_file.write("\" z=\"")
    geometry_file.write(str(maxL))
    side = float(line.split()[2])
    geometry_file.write("\" lunit=\"cm\"/>\n")
    position_file.write("<position name=\"pos_");
    position_file.write(name);
    position_file.write("\" x=\"0.0\" y=\"0.0\" z=\"")
    position_file.write(str(side+0.5*maxL+tra_dz))
    position_file.write("\" /> \n")
    position_file.write("<rotation name=\"rot_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(rot_dx))
    position_file.write("\" y=\"")
    position_file.write(str(rot_dy))
    position_file.write("\" z=\"")
    position_file.write(str(rot_dz))
    position_file.write("\" unit=\"deg\"/> \n")

def importXZP(line):
    name = line.split()[1]
    geometry_file.write("<box name=\"")
    geometry_file.write(name)
    geometry_file.write("\" x=\"")
    geometry_file.write(str(maxL))
    geometry_file.write("\" y=\"")
    geometry_file.write(str(maxL))
    geometry_file.write("\" z=\"")
    geometry_file.write(str(maxL))
    side = float(line.split()[2])
    geometry_file.write("\" lunit=\"cm\"/>\n")
    position_file.write("<position name=\"pos_");
    position_file.write(name);
    position_file.write("\" x=\"0.0\" z=\"0.0\" y=\"")
    position_file.write(str(side+0.5*maxL+tra_dy))
    position_file.write("\" /> \n")
    position_file.write("<rotation name=\"rot_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(rot_dx))
    position_file.write("\" y=\"")
    position_file.write(str(rot_dy))
    position_file.write("\" z=\"")
    position_file.write(str(rot_dz))
    position_file.write("\" unit=\"deg\"/> \n")

def importYZP(line):
    name = line.split()[1]
    geometry_file.write("<box name=\"")
    geometry_file.write(name)
    geometry_file.write("\" x=\"")
    geometry_file.write(str(maxL))
    geometry_file.write("\" y=\"")
    geometry_file.write(str(maxL))
    geometry_file.write("\" z=\"")
    geometry_file.write(str(maxL))
    side = float(line.split()[2])
    geometry_file.write("\" lunit=\"cm\"/>\n")
    position_file.write("<position name=\"pos_");
    position_file.write(name);
    position_file.write("\" z=\"0.0\" y=\"0.0\" x=\"")
    position_file.write(str(side+0.5*maxL+tra_dx))
    position_file.write("\" /> \n")
    position_file.write("<rotation name=\"rot_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(rot_dx))
    position_file.write("\" y=\"")
    position_file.write(str(rot_dy))
    position_file.write("\" z=\"")
    position_file.write(str(rot_dz))
    position_file.write("\" unit=\"deg\"/> \n")


def importXCC(line):
    name = line.split()[1]
    geometry_file.write("<tube name=\"")
    geometry_file.write(name)
    yval=float(line.split()[2])
    zval=float(line.split()[3])
    Rval=float(line.split()[4])
    geometry_file.write("\" rmin=\"0.0\" rmax=\"")
    geometry_file.write(str(Rval))
    geometry_file.write("\" z=\"")
    geometry_file.write(str(maxL))
    geometry_file.write("\" deltaphi=\"360\" startphi=\"0.0\" aunit=\"deg\" lunit=\"cm\"/>\n")
    position_file.write("<position name=\"pos_");
    position_file.write(name);
    position_file.write("\" x=\"0.0\" y=\"")
    position_file.write(str(yval+tra_dy))
    position_file.write("\" z=\"")
    position_file.write(str(zval+tra_dz))
    position_file.write("\" /> \n")
    position_file.write("<rotation name=\"rot_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(rot_dx))
    position_file.write("\" y=\"")
    position_file.write(str(rot_dy+HALFPI))
    position_file.write("\" z=\"")
    position_file.write(str(rot_dz))
    position_file.write("\" unit=\"deg\"/> \n")


def importYCC(line):
    name = line.split()[1]
    geometry_file.write("<tube name=\"")
    geometry_file.write(name)
    zval=float(line.split()[2])
    xval=float(line.split()[3])
    Rval=float(line.split()[4])
    geometry_file.write("\" rmin=\"0.0\" rmax=\"")
    geometry_file.write(str(Rval))
    geometry_file.write("\" z=\"")
    geometry_file.write(str(maxL))
    geometry_file.write("\" deltaphi=\"360\" startphi=\"0.0\" aunit=\"deg\" lunit=\"cm\"/>\n")
    position_file.write("<position name=\"pos_");
    position_file.write(name);
    position_file.write("\" y=\"0.0\" x=\"")
    position_file.write(str(xval+tra_dx))
    position_file.write("\" z=\"")
    position_file.write(str(zval+tra_dz))
    position_file.write("\" /> \n")
    position_file.write("<rotation name=\"rot_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(rot_dx+HALFPI))
    position_file.write("\" y=\"")
    position_file.write(str(rot_dy))
    position_file.write("\" z=\"")
    position_file.write(str(rot_dz))
    position_file.write("\" unit=\"deg\"/> \n")

def importZCC(line):
    name = line.split()[1]
    geometry_file.write("<tube name=\"")
    geometry_file.write(name)
    xval=float(line.split()[2])
    yval=float(line.split()[3])
    Rval=float(line.split()[4])
    geometry_file.write("\" rmin=\"0.0\" rmax=\"")
    geometry_file.write(str(Rval))
    geometry_file.write("\" z=\"")
    geometry_file.write(str(maxL))
    geometry_file.write("\" deltaphi=\"360\" startphi=\"0.0\" aunit=\"deg\" lunit=\"cm\"/>\n")
    position_file.write("<position name=\"pos_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(xval+tra_dx))
    position_file.write("\" y=\"")
    position_file.write(str(yval+tra_dy))
    position_file.write("\" zval=\"0.0\" /> \n")
    position_file.write("<rotation name=\"rot_");
    position_file.write(name);
    position_file.write("\" x=\"")
    position_file.write(str(rot_dx))
    position_file.write("\" y=\"")
    position_file.write(str(rot_dy))
    position_file.write("\" z=\"")
    position_file.write(str(rot_dz))
    position_file.write("\" unit=\"deg\"/> \n")


at_RPP = 0
at_RPP2 = 0
at_RCC = 0
at_RCC2 = 0
at_TRC = 0
at_TRC2 = 0
at_ELL = 0
at_ELL2 = 0

for line in input_file:
    
    if line.startswith("MATERIAL"):
        import_material(line)
    pass

    
    if line.startswith("$start_transform"):
        name= line.split()[1]
        print str(name) + "\n"
        import_rot_defi(name)
    pass

    if line.startswith("$end_transform"):
        import_end_rot_defi()
    pass

    if line.startswith("$start_translat"):
        import_start_translat(line)
    pass


    if line.startswith("$end_translat"):
        import_end_translat(line)
    pass

    if line.startswith("RPP"):
        at_RPP = 1
        at_RPP2 = 0
    pass
    if at_RPP2 == 1:
        line2 = line
        importRPPlong(line1,line2)
        at_RPP2 = 0
    pass
    if at_RPP == 1:
        if len(line.split()) < RPP_lenght:
            if line.startswith("RPP"):
                line1 = line
                at_RPP = 0
                at_RPP2 = 1
            pass
        else:
            importRPP(line)
            at_RPP = 0
        pass
    pass

    if line.startswith("SPH"):

        importSPH(line)
    pass

    if line.startswith("XYP"):

        importXYP(line)
    pass

    if line.startswith("XZP"):

        importXZP(line)
    pass


    if line.startswith("YZP"):

        importYZP(line)
    pass

    if line.startswith("XCC"):
 
        importXCC(line)
    pass

    if line.startswith("YCC"):
 
        importYCC(line)
    pass

    if line.startswith("ZCC"):

        importZCC(line)
    pass


    if line.startswith("RCC"):
        at_RCC = 1
        at_RCC2 = 0
    pass
    if at_RCC2 == 1:
        line2 = line
        importRCClong(line1,line2)
        at_RCC2 = 0
    pass
    if at_RCC == 1:
        if len(line.split()) < RCC_lenght:
            if line.startswith("RCC"):
                line1 = line
                at_RCC = 0
                at_RCC2 = 1
            pass
        else:
            importRCC(line)
            at_RCC = 0
        pass
    pass



    if line.startswith("TRC"):
        at_TRC = 1
        at_TRC2 = 0
    pass
    if at_TRC2 == 1:
        line2 = line
        importTRClong(line1,line2)
        at_TRC2 = 0
    pass
    if at_TRC == 1:
        if len(line.split()) < TRC_lenght:
            if line.startswith("TRC"):
                line1 = line
                at_TRC = 0
                at_TRC2 = 1
            pass
        else:
            importTRC(line)
            at_TRC = 0
        pass
    pass


    if line.startswith("ELL"):
        at_ELL = 1
        at_ELL2 = 0
    pass
    if at_ELL2 == 1:
        line2 = line
        importELLlong(line1,line2)
        at_ELL2 = 0
    pass
    if at_ELL == 1:
        if len(line.split()) < ELL_lenght:
            if line.startswith("ELL"):
                line1 = line
                at_ELL = 0
                at_ELL2 = 1
            pass
        else:
            importELL(line)
            at_ELL = 0
        pass
    pass


    continue
#Go back at the start to the input file
# We need to parse again the input file, since rotation can be defined after the region is called
input_file.seek(0)
at_region = 0
at_region2 = 0
len_region = 0
region_list_id = 1
rvalue = {}        
for line in input_file:
    if len(line.split()) > 1 and at_region > 0 and line.split()[1] != "5" and line.split()[0] != "*" :
        for x in range(len(line.split())):
            rvalue[int(at_region-1),len_region + int(x)] = line.split()[int(x)]   
        print str(at_region) + " " + str(len_region)
        len_region = len_region + int(len(line.split()))
    pass
    if len(line.split()) > 1 and line.split()[1] == "5" :
        at_region = at_region + 1
        at_region2 = at_region2 + 1
        len_region = int(len(line.split()) - 1)
        print "REGION " + line.split()[0]
        rvalue[int(at_region-1),0] = line.split()[0]
        for x in range(2,len(line.split())):
            rvalue[int(at_region-1),int(x)-1] = line.split()[int(x)]
    pass
    if line.startswith("END"):
        at_region = 0
    pass
    if line.startswith("GEOEND"):
        at_region = 0
    pass

    continue


print "total number of regions =" + str(at_region2) 

#in this variable I am going to store how many volumes are inside a subregion MAX=100 subregions
reg_n_at_subreg = []
for i in range(100):
    reg_n_at_subreg.append(i)

for i in range(at_region2):
    j = 0
    at_val = 1
    reg_n = 1
    subreg_n = 0
    parent_n = 0
    subparen_n = 0
    while at_val == 1 :
        print str(i) + " " +  str(j) + " " + rvalue[i,j]
        if j==0:
            # I assume here that the first volume is called with a +
            geometry_file.write("<intersection name=\"")
            geometry_file.write(rvalue[i,0])
            geometry_file.write("_0_0\"> \n")
            geometry_file.write("<first ref=\"BoxMother\"/> \n")
            geometry_file.write("<second ref=\"")
            bodyname = rvalue[i,1].replace("+","")
            geometry_file.write(bodyname)
            geometry_file.write("\"/> \n")
            geometry_file.write("<positionref ref=\"")
            posname = rvalue[i,1].replace("+","pos_")
            geometry_file.write(posname)
            geometry_file.write("\"/> \n")
            geometry_file.write("<rotationref ref=\"")
            rotname = rvalue[i,1].replace("+","rot_")
            geometry_file.write(rotname)
            geometry_file.write("\"/> \n")
            geometry_file.write("</intersection> \n")
            j=1
        pass

        # j=1 is already taken care of, from j=2
        if j>1:

            if rvalue[i,j].startswith("-") and len(rvalue[i,j]) > 2 :
                geometry_file.write("<subtraction name=\"")
                geometry_file.write(rvalue[i,0])
                geometry_file.write("_")
                geometry_file.write(str(subreg_n))
                geometry_file.write("_")
                geometry_file.write(str(reg_n))
                geometry_file.write("\"> \n")
                geometry_file.write("<first ref=\"")
                geometry_file.write(rvalue[i,0])
                geometry_file.write("_")
                geometry_file.write(str(subreg_n))
                geometry_file.write("_")
                geometry_file.write(str(reg_n-1))
                geometry_file.write("\"/> \n")
                geometry_file.write("<second ref=\"")
                bodyname = rvalue[i,j].replace("-","")
                geometry_file.write(bodyname)
                geometry_file.write("\"/> \n")
                geometry_file.write("<positionref ref=\"")
                posname = rvalue[i,j].replace("-","pos_")
                geometry_file.write(posname)
                geometry_file.write("\"/> \n")
                geometry_file.write("<rotationref ref=\"")
                rotname = rvalue[i,j].replace("-","rot_")
                geometry_file.write(rotname)
                geometry_file.write("\"/> \n")
                geometry_file.write("</subtraction> \n")
                reg_n +=1
            elif rvalue[i,j].startswith("+") and len(rvalue[i,j]) > 2 :
                geometry_file.write("<intersection name=\"")
                geometry_file.write(rvalue[i,0])
                geometry_file.write("_")
                geometry_file.write(str(subreg_n))
                geometry_file.write("_")
                geometry_file.write(str(reg_n))
                geometry_file.write("\"> \n")
                geometry_file.write("<first ref=\"")
                geometry_file.write(rvalue[i,0])
                geometry_file.write("_")
                geometry_file.write(str(subreg_n))
                geometry_file.write("_")
                geometry_file.write(str(reg_n-1))
                geometry_file.write("\"/> \n")
                geometry_file.write("<second ref=\"")
                bodyname = rvalue[i,j].replace("+","")
                geometry_file.write(bodyname)
                geometry_file.write("\"/> \n")
                geometry_file.write("<positionref ref=\"")
                posname = rvalue[i,j].replace("+","pos_")
                geometry_file.write(posname)
                geometry_file.write("\"/> \n")
                geometry_file.write("<rotationref ref=\"")
                rotname = rvalue[i,j].replace("+","rot_")
                geometry_file.write(rotname)
                geometry_file.write("\"/> \n")
                geometry_file.write("</intersection> \n")
                reg_n +=1
            elif rvalue[i,j].startswith("|") and len(rvalue[i,j]) > 2 :
                geometry_file.write("<union name=\"")
                geometry_file.write(rvalue[i,0])
                geometry_file.write("_")
                geometry_file.write(str(subreg_n))
                geometry_file.write("_")
                geometry_file.write(str(reg_n))
                geometry_file.write("\"> \n")
                geometry_file.write("<first ref=\"")
                geometry_file.write(rvalue[i,0])
                geometry_file.write("_")
                geometry_file.write(str(subreg_n))
                geometry_file.write("_")
                geometry_file.write(str(reg_n-1))
                geometry_file.write("\"/> \n")
                geometry_file.write("<second ref=\"")
                bodyname = rvalue[i,j].replace("|","")
                geometry_file.write(bodyname)
                geometry_file.write("\"/> \n")
                geometry_file.write("<positionref ref=\"")
                posname = rvalue[i,j].replace("|","pos_")
                geometry_file.write(posname)
                geometry_file.write("\"/> \n")
                geometry_file.write("<rotationref ref=\"")
                rotname = rvalue[i,j].replace("|","rot_")
                geometry_file.write(rotname)
                geometry_file.write("\"/> \n")
                geometry_file.write("</union> \n")
                reg_n +=1
            elif rvalue[i,j] == "|":
                #Here I am assuming is a subregion: This will start with a plus as before
                reg_n_at_subreg[int(subreg_n)] = reg_n
                print "subreg n" + str(subreg_n) + " volumes = " + str(reg_n)
                subreg_n += 1
                reg_n = 0
                geometry_file.write("<intersection name=\"")
                geometry_file.write(rvalue[i,0])
                geometry_file.write("_")
                geometry_file.write(str(subreg_n))
                geometry_file.write("_0\"> \n")
                geometry_file.write("<first ref=\"BoxMother\"/> \n")
                geometry_file.write("<second ref=\"")
                bodyname = rvalue[i,j+1].replace("+","")
                geometry_file.write(bodyname)
                geometry_file.write("\"/> \n")
                geometry_file.write("<positionref ref=\"")
                posname = rvalue[i,j+1].replace("+","pos_")
                geometry_file.write(posname)
                geometry_file.write("\"/> \n")
                geometry_file.write("<rotationref ref=\"")
                rotname = rvalue[i,j+1].replace("+","rot_")
                geometry_file.write(rotname)
                geometry_file.write("\"/> \n")
                geometry_file.write("</intersection> \n")
                j += 1
                reg_n +=1
            elif len(rvalue[i,j])> 1 and rvalue[i,j][1] == "(":
                parent_op = rvalue[i,j][0]
                print "Parenthesis open \n"
                j += 1
                geometry_file.write("<intersection name=\"")
                geometry_file.write(rvalue[i,0])
                geometry_file.write("_")
                geometry_file.write(str(subreg_n))
                geometry_file.write("_")
                geometry_file.write(str(reg_n))
                geometry_file.write("_")
                geometry_file.write(str(parent_n))
                geometry_file.write("\"> \n")
                geometry_file.write("<first ref=\"BoxMother\"/> \n")
                geometry_file.write("<second ref=\"")
                bodyname = rvalue[i,j].replace("+","")
                geometry_file.write(bodyname)
                geometry_file.write("\"/> \n")
                geometry_file.write("<positionref ref=\"")
                posname = rvalue[i,j].replace("+","pos_")
                geometry_file.write(posname)
                geometry_file.write("\"/> \n")
                geometry_file.write("<rotationref ref=\"")
                rotname = rvalue[i,j].replace("+","rot_")
                geometry_file.write(rotname)
                geometry_file.write("\"/> \n")
                geometry_file.write("</intersection> \n")
                parent_n += 1
                j += 1
                while rvalue[i,j] != ")" :
                    if rvalue[i,j].startswith("-") and len(rvalue[i,j]) > 2 :
                        geometry_file.write("<subtraction name=\"")
                        geometry_file.write(rvalue[i,0])
                        geometry_file.write("_")
                        geometry_file.write(str(subreg_n))
                        geometry_file.write("_")
                        geometry_file.write(str(reg_n))
                        geometry_file.write("_")
                        geometry_file.write(str(parent_n))
                        geometry_file.write("\"> \n")
                        geometry_file.write("<first ref=\"")
                        geometry_file.write(rvalue[i,0])
                        geometry_file.write("_")
                        geometry_file.write(str(subreg_n))
                        geometry_file.write("_")
                        geometry_file.write(str(reg_n))
                        geometry_file.write("_")
                        geometry_file.write(str(parent_n-1))
                        geometry_file.write("\"/> \n")
                        geometry_file.write("<second ref=\"")
                        bodyname = rvalue[i,j].replace("-","")
                        geometry_file.write(bodyname)
                        geometry_file.write("\"/> \n")
                        geometry_file.write("<positionref ref=\"")
                        posname = rvalue[i,j].replace("-","pos_")
                        geometry_file.write(posname)
                        geometry_file.write("\"/> \n")
                        geometry_file.write("<rotationref ref=\"")
                        rotname = rvalue[i,j].replace("-","rot_")
                        geometry_file.write(rotname)
                        geometry_file.write("\"/> \n")
                        geometry_file.write("</subtraction> \n")
                        parent_n +=1
                        j +=1
                    elif rvalue[i,j].startswith("+") and len(rvalue[i,j]) > 2 :
                        geometry_file.write("<intersection name=\"")
                        geometry_file.write(rvalue[i,0])
                        geometry_file.write("_")
                        geometry_file.write(str(subreg_n))
                        geometry_file.write("_")
                        geometry_file.write(str(reg_n))
                        geometry_file.write("_")
                        geometry_file.write(str(parent_n))
                        geometry_file.write("\"> \n")
                        geometry_file.write("<first ref=\"")
                        geometry_file.write(rvalue[i,0])
                        geometry_file.write("_")
                        geometry_file.write(str(subreg_n))
                        geometry_file.write("_")
                        geometry_file.write(str(reg_n))
                        geometry_file.write("_")
                        geometry_file.write(str(parent_n-1))
                        geometry_file.write("\"/> \n")
                        geometry_file.write("<second ref=\"")
                        bodyname = rvalue[i,j].replace("+","")
                        geometry_file.write(bodyname)
                        geometry_file.write("\"/> \n")
                        geometry_file.write("<positionref ref=\"")
                        posname = rvalue[i,j].replace("+","pos_")
                        geometry_file.write(posname)
                        geometry_file.write("\"/> \n")
                        geometry_file.write("<rotationref ref=\"")
                        rotname = rvalue[i,j].replace("+","rot_")
                        geometry_file.write(rotname)
                        geometry_file.write("\"/> \n")
                        geometry_file.write("</intersection> \n")
                        parent_n +=1
                        j +=1
                    elif rvalue[i,j].startswith("|") and len(rvalue[i,j]) > 2 :
                        geometry_file.write("<union name=\"")
                        geometry_file.write(rvalue[i,0])
                        geometry_file.write("_")
                        geometry_file.write(str(subreg_n))
                        geometry_file.write("_")
                        geometry_file.write(str(reg_n))
                        geometry_file.write("_")
                        geometry_file.write(str(parent_n))
                        geometry_file.write("\"> \n")
                        geometry_file.write("<first ref=\"")
                        geometry_file.write(rvalue[i,0])
                        geometry_file.write("_")
                        geometry_file.write(str(subreg_n))
                        geometry_file.write("_")
                        geometry_file.write(str(reg_n))
                        geometry_file.write("_")
                        geometry_file.write(str(parent_n-1))
                        geometry_file.write("\"/> \n")
                        geometry_file.write("<second ref=\"")
                        bodyname = rvalue[i,j].replace("|","")
                        geometry_file.write(bodyname)
                        geometry_file.write("\"/> \n")
                        geometry_file.write("<positionref ref=\"")
                        posname = rvalue[i,j].replace("|","pos_")
                        geometry_file.write(posname)
                        geometry_file.write("\"/> \n")
                        geometry_file.write("<rotationref ref=\"")
                        rotname = rvalue[i,j].replace("|","rot_")
                        geometry_file.write(rotname)
                        geometry_file.write("\"/> \n")
                        geometry_file.write("</union> \n")
                        parent_n +=1
                        j +=1
                    pass
                print "found end parenthesis \n"
                if parent_op == "+" :
                    geometry_file.write("<intersection name=\"")
                    geometry_file.write(rvalue[i,0])
                    geometry_file.write("_")
                    geometry_file.write(str(subreg_n))
                    geometry_file.write("_")
                    geometry_file.write(str(reg_n))
                    geometry_file.write("\"> \n")
                    geometry_file.write("<first ref=\"")
                    geometry_file.write(rvalue[i,0])
                    geometry_file.write("_")
                    geometry_file.write(str(subreg_n))
                    geometry_file.write("_")
                    geometry_file.write(str(reg_n-1))
                    geometry_file.write("\"/> \n")
                    geometry_file.write("<second ref=\"")
                    geometry_file.write(rvalue[i,0])
                    geometry_file.write("_")
                    geometry_file.write(str(subreg_n))
                    geometry_file.write("_")
                    geometry_file.write(str(reg_n))
                    geometry_file.write("_")
                    geometry_file.write(str(parent_n-1))
                    geometry_file.write("\"/> \n")
                    geometry_file.write("<positionref ref=\"center\"/> \n")
                    geometry_file.write("<rotationref ref=\"identity\"/> \n")
                    geometry_file.write("</intersection> \n")
                    reg_n +=1
                elif parent_op == "-" : 
                    geometry_file.write("<subtraction name=\"")
                    geometry_file.write(rvalue[i,0])
                    geometry_file.write("_")
                    geometry_file.write(str(subreg_n))
                    geometry_file.write("_")
                    geometry_file.write(str(reg_n))
                    geometry_file.write("\"> \n")
                    geometry_file.write("<first ref=\"")
                    geometry_file.write(rvalue[i,0])
                    geometry_file.write("_")
                    geometry_file.write(str(subreg_n))
                    geometry_file.write("_")
                    geometry_file.write(str(reg_n-1))
                    geometry_file.write("\"/> \n")
                    geometry_file.write("<second ref=\"")
                    geometry_file.write(rvalue[i,0])
                    geometry_file.write("_")
                    geometry_file.write(str(subreg_n))
                    geometry_file.write("_")
                    geometry_file.write(str(reg_n))
                    geometry_file.write("_")
                    geometry_file.write(str(parent_n-1))
                    geometry_file.write("\"/> \n")
                    geometry_file.write("<positionref ref=\"center\"/> \n")
                    geometry_file.write("<rotationref ref=\"identity\"/> \n")
                    geometry_file.write("</subtraction> \n")
                    reg_n +=1

                elif parent_op == "|" :
                    geometry_file.write("<union name=\"")
                    geometry_file.write(rvalue[i,0])
                    geometry_file.write("_")
                    geometry_file.write(str(subreg_n))
                    geometry_file.write("_")
                    geometry_file.write(str(reg_n))
                    geometry_file.write("\"> \n")
                    geometry_file.write("<first ref=\"")
                    geometry_file.write(rvalue[i,0])
                    geometry_file.write("_")
                    geometry_file.write(str(subreg_n))
                    geometry_file.write("_")
                    geometry_file.write(str(reg_n-1))
                    geometry_file.write("\"/> \n")
                    geometry_file.write("<second ref=\"")
                    geometry_file.write(rvalue[i,0])
                    geometry_file.write("_")
                    geometry_file.write(str(subreg_n))
                    geometry_file.write("_")
                    geometry_file.write(str(reg_n))
                    geometry_file.write("_")
                    geometry_file.write(str(parent_n-1))
                    geometry_file.write("\"/> \n")
                    geometry_file.write("<positionref ref=\"center\"/> \n")
                    geometry_file.write("<rotationref ref=\"identity\"/> \n")
                    geometry_file.write("</union> \n")
                    reg_n +=1
                pass
                        
                parent_n = 0
            pass
            at_val = 1
        j += 1
        try:
            rvalue[i,j]
        except KeyError:
            # Here I should reconstruct all the subregions since the array is finished
            reg_n_at_subreg[int(subreg_n)] = reg_n
            print "subreg n" + str(subreg_n) + " volumes = " + str(reg_n)
            geometry_file.write("<intersection name=\"")
            geometry_file.write(rvalue[i,0])
            geometry_file.write("_")
            geometry_file.write(str(subreg_n))
            geometry_file.write("\"> \n")
            geometry_file.write("<first ref=\"BoxMother\"/> \n")
            geometry_file.write("<second ref=\"")
            geometry_file.write(rvalue[i,0])
            geometry_file.write("_0_")
            geometry_file.write(str(reg_n_at_subreg[0]-1))
            geometry_file.write("\"/> \n")           
            geometry_file.write("<positionref ref=\"center\"/> \n")
            geometry_file.write("<rotationref ref=\"identity\"/> \n")
            geometry_file.write("</intersection> \n")

            insertValues = "INSERT INTO region_list values(" + str(region_list_id) + ",\"" + str(rvalue[i,0]) + "\")"    
            cursorObject.execute(insertValues)
            region_list_id +=1
            
            if (subreg_n > 0) : 
                for k in range(1,subreg_n+1):
                    geometry_file.write("<union name=\"")
                    geometry_file.write(rvalue[i,0])
                    geometry_file.write("_")
                    geometry_file.write(str(subreg_n - k))
                    geometry_file.write("\"> \n")
                    geometry_file.write("<first ref=\"")
                    geometry_file.write(rvalue[i,0])
                    geometry_file.write("_")
                    geometry_file.write(str(subreg_n - k + 1))
                    geometry_file.write("\"/> \n")
                    geometry_file.write("<second ref=\"")
                    geometry_file.write(rvalue[i,0])
                    geometry_file.write("_")
                    geometry_file.write(str(k))
                    geometry_file.write("_")
                    geometry_file.write(str(reg_n_at_subreg[k]-1))
                    geometry_file.write("\"/> \n")           
                    geometry_file.write("<positionref ref=\"center\"/> \n")
                    geometry_file.write("<rotationref ref=\"identity\"/> \n")
                    geometry_file.write("</union> \n")
            pass
            at_val = 0
        else:
            at_val = 1

#Go back at the start to the input file
# We need to parse again the input file, since material can be defined after the region is called
input_file.seek(0)

#Finished to write geometry part, now I need to assign volumes and physical volumes
geometry_file.write("</solids> \n")
geometry_file.write("<structure> \n")


#Now associate region to material and place it
for line in input_file:
    
    if line.startswith("ASSIGNMA"):
        import_assigma(line)
    pass


    continue


#Now write the material left in the file
query_str = "SELECT * FROM material_infile where towrite='1'"
cursorObject.execute(query_str)
records = cursorObject.fetchall()
if records != None:
    for record in records:
        material_file.write("<material name=\"mat_")
        material_file.write(str(record[1]))
        material_file.write("\" Z=\"")
        material_file.write(str(record[3]))
        material_file.write("\"> <D value=\"")
        material_file.write(str(record[5]))
        material_file.write("\"/> <atom value=\"")
        material_file.write(str(record[4]))
        material_file.write("\"/>  </material> \n")
        material_file.write("<element name=\"el_")
        material_file.write(str(record[1]))
        material_file.write("\" formula=\"")
        material_file.write(str(record[2]))
        material_file.write("\" Z=\"")
        material_file.write(str(record[3]))
        material_file.write("\"> <atom value=\"")
        material_file.write(str(record[4]))
        material_file.write("\"/> </element> \n")


#Now go trough the list of regions and write down the placement of physical volumes.
#Since all the volumes have been created already at the right location, I can just place it at the center with no rotation needed
query_str = "SELECT * FROM region_list"
cursorObject.execute(query_str)
records = cursorObject.fetchall()
geometry_file.write("<volume name=\"vol_")
geometry_file.write("BoxMother")
geometry_file.write("\"> \n  <materialref ref=\"mat_")
geometry_file.write("BLCKHOLE")
geometry_file.write("\"/> \n  <solidref ref=\"")
geometry_file.write("BoxMother")
geometry_file.write("\"/> \n")

if records != None:
    for record in records:
        geometry_file.write("<physvol> \n  <volumeref ref=\"vol_")
        geometry_file.write(str(record[1]))
        geometry_file.write("\"/> \n  <positionref ref=\"center\"/> \n  <rotationref ref=\"identity\"/> \n </physvol> \n") 


geometry_file.write("</volume> \n")

#Close the files
position_file.write("</define> \n")
material_file.write("</materials> \n")
geometry_file.write("</structure> \n")

geometry_file.write("<setup name=\"Default\" version=\"1.0\"> \n")
geometry_file.write("  <world ref=\"vol_BoxMother\"/> \n")
geometry_file.write("</setup> \n")
        
geometry_file.close()
position_file.close()
material_file.close()

connectionObject.close()


#now create output file with full geometry

data1 = data2 = data3 = ""

with open(position_file_name) as fileout:
    data1 = fileout.read()

with open(material_file_name) as fileout:
    data2 = fileout.read()

data1 += "\n \n"
data1 += data2

with open(geometry_file_name) as fileout:
    data3 = fileout.read()

data1 += "\n \n"
data1 += data3

with open ('output.gdml','w') as fileout:
    fileout.write("<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\" ?> \n <gdml xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:noNamespaceSchemaLocation=\"http://service-spi.web.cern.ch/service-spi/app/releases/GDML/schema/gdml.xsd\"> \n \n")
    fileout.write(data1)
    fileout.write("\n \n </gdml> \n")

