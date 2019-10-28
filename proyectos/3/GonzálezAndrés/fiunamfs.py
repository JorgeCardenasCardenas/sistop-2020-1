from mmap import mmap
import re
import math
from datetime import datetime #, strptime
import os

MSGERR_NO_MONTADO = 'Error: No se ha montado el sistema de archivos'
MSGERR_ARCH_NO_ENC = 'Error: No se encuentra el archivo de origen'
MSGADV_FS_YA_MONT = 'Advertencia: El sistema de archivos ya está montado'
MSGERR_FN_INVALIDO = 'Error: el tamaño del nombre del archivo debe ser de 1 a 15 caracteres y estos deben ser US-ASCII imprimibles'
PATRON_FN_VALIDO = re.compile(r'[\x21-\x7F][\x20-\x7F]{,14}') # Patrón para verificar si los archivos tienen caracteres válidos
STR_DIR_VACIO = 'Xx.xXx.xXx.xXx.'
NOMBRE_FS = 'FiUnamFS'

def now():
    return datetime.now().strftime('%Y%m%d%H%M%S')#.encode('ascii')

def format_date(datestr : str):
    return '%4s/%2s/%2s %2s:%2s' % (datestr[0:4], datestr[4:6], datestr[6:8], datestr[8:10], datestr[10:12])

class FIUNAMFS(object):
    def __init__(self, ruta_img):
        self.ruta_img = ruta_img
        self.__listaEntDir = []
        self.montado = False
    
    def __del__(self):
        if self.montado == True:
            self.desmontar()

    def montar(self):
        if self.montado:   
            print(MSGADV_FS_YA_MONT)
            return True 
                    
        try:
            self.__f = open(self.ruta_img, 'r+b')
        except OSError as oserr:
            print('OSError: %s' % oserr)
        except IOError as ioerr:
            print('IOError %s' % ioerr)
        else:
            self.__mmfs = mmap(self.__f.fileno(), 0)
            nombrefs = self.__mmfs[0:8].decode('ascii')
            # print(nombrefs)
            if nombrefs == NOMBRE_FS:
                self.montado = True

                self.nombre = nombrefs
                # print('Nombre del sistema de archivos: %s' % self.nombre)

                self.version = self.__mmfs[10:13].decode('ascii').strip()
                # print('Versión: %s' % self.version)
                
                self.etiqueta = self.__mmfs[20:35].decode('ascii').strip()
                # print('Etiqueta del volumen: %s' % self.etiqueta)
                
                self.tam_cluster = int(self.__mmfs[40:45].decode('ascii').strip())
                # print('Tamaño del cluster: %i bytes' % self.tam_cluster)

                self.clusters_dir = int(self.__mmfs[47:49].decode('ascii').strip())
                # print('Tamaño del directorio: %i clusters' % self.clusters_dir)

                self.clusters_totales = int(self.__mmfs[52:60].decode('ascii').strip())
                # print('Tamaño de la unidad: %i clusters' % self.clusters_totales)

                self.tam_entradadir = 64

                self.tam_dir = self.tam_cluster * self.clusters_dir

                self.scandir()

                print('Sistema de archivos montado')
                return True
            else:
                print('No se reconoce el sistema de archivos')
                self.__mmfs.close()
                self.montado = False
                return False

    def desmontar(self):
        if self.montado:
            self.__mmfs.close()
            self.__f.close()
            self.montado = False
            print('Sistema de archivos desmontado')
        else:
            print(MSGERR_NO_MONTADO)

    def listdir(self):
        ldir = []
        if self.montado:
            for entradaDir in self.__listaEntDir:
                ldir.append(entradaDir.nombre)
        else: 
            print(MSGERR_NO_MONTADO)
        return ldir
    
    def scandir(self):
        self.__listaEntDir = []
        if not self.montado:
            print(MSGERR_NO_MONTADO)
            return []
        
        inicio = self.tam_cluster
        fin = self.tam_dir+self.tam_cluster
        paso = self.tam_entradadir
        for i in range(inicio,fin,paso):
            entdir = self.__mmfs[i:i+paso]
            nombre = entdir[0:15].decode('ascii').strip()
            if nombre != STR_DIR_VACIO:
                tam_archivo = int(entdir[16:24].decode('ascii').strip())
                cluster_inicial = int(entdir[25:30].decode('ascii').strip())
                f_creacion = entdir[31:45].decode('ascii')
                f_modif = entdir[46:60].decode('ascii')
                nuevaEntrada = EntradaDir(nombre, tam_archivo, cluster_inicial, f_creacion, f_modif, i)
                self.__listaEntDir.append(nuevaEntrada)            
        return self.__listaEntDir

    def descargar(self, origen = '', destino = ''):
        """Copiar un archivo de FIUNAMFS a nuestro sistema de archivos
        Atributos:
            origen -- nombre del archivo a copiar
            destino -- ruta y nombre del archivo de destino
        """
        if not self.montado:
            print(MSGERR_NO_MONTADO)
            return False

        resultado = list(filter( lambda entdir: entdir.nombre == origen, self.__listaEntDir)) # Buscamos el elemento que coincida
        if not resultado:
            print(MSGERR_ARCH_NO_ENC)
            return False
        
        entrDir = resultado.pop() # Obtenemos la entrada del directorio
        dir_inicio = entrDir.cluster_inicial * self.tam_cluster # dirección de inicio
        dir_fin = dir_inicio + entrDir.tam_archivo # dirección de fin
        bytes_archivo = self.__mmfs[dir_inicio:dir_fin] # bytes en bruto
        try:
            destino = origen if not destino else destino # Usar el mismo nombre que el del origen si no le dimos ninguno
            f = open(destino, 'w+b') # Abrimos el archivo en modo w+b
            f.write(bytes_archivo)
            f.close()
            print('Se escribió el archivo %s' % destino)
            return True
        except IOError as ioerr:
            print('IOError: %s' % ioerr)            
    
    def subir(self, origen, destino=''):
        if not self.montado:
            print(MSGERR_NO_MONTADO)
            return False
        try:
            f = open(origen, 'rb') # Abrimos el archivo en modo lectura
            bytes_archivo = f.read()
            tam_archivo = len(bytes_archivo)
            clusters_requeridos = math.ceil(tam_archivo / self.tam_cluster)
            print('Tamaño de "%s": %i bytes, %i clusters' % (origen, tam_archivo, clusters_requeridos))
            f.close()

            destino = destino.strip() # Le quitamos los caracteres en blanco al inicio y al final
            if not destino:
                destino = origen # Si no se nombre de archivo de destino, usamos el de origen

            if not re.fullmatch(PATRON_FN_VALIDO, destino): # Checamos si el nombre de destino cumple con el patrón
                print(MSGERR_FN_INVALIDO)
                print('Nombre ingresado: %s' % destino)
                return False

            # Ahora revisaré si hay espacio en disco y dónde iniciaremos a grabar el archivo
            # Iniciar valores en límites fuera de rango para no sobreescribir información en caso de error
            cluster_inicial = self.clusters_totales - 1
            clusters_libres = 0
            if not self.__listaEntDir:
                print('Directorio vacío, guardando archivo en el primer cluster de datos')
                cluster_inicial = self.clusters_dir + 1 # Clusters de directorio + Cluster de SB
                clusters_libres = self.clusters_totales - cluster_inicial # Calcular clusters libres
            else:
                resultado = list(filter( lambda entdir: entdir.nombre == destino, self.__listaEntDir)) # Buscamos si hay algún archivo con el mismo nombre
                if resultado:
                    print('Ya existe un archivo con ese nombre en el directorio: %s' % destino)
                    return False
                
                self.__listaEntDir = sorted(self.__listaEntDir, key=lambda ed: ed.cluster_inicial) # Ordenamos la lista de entradas con base en el cluster donde inician
                for i, ed_actual in enumerate(self.__listaEntDir): # ed_actual : entrada del directorio actual
                    clusters_usados = math.ceil(ed_actual.tam_archivo / self.tam_cluster) # Clusters usados por el archivo i-ésimo
                    try:
                        ed_sig = self.__listaEntDir[i+1] # ed_sig : entrada del directorio siguiente
                        delta_clusters = ed_sig.cluster_inicial - ed_actual.cluster_inicial # vemos cuántos clusters hay entre entrada de directorio y entrada de directorio
                        clusters_libres = delta_clusters - clusters_usados
                        cluster_inicial = ed_actual.cluster_inicial + clusters_usados # Marcamos la dirección de inicio 

                    except IndexError:
                        print('Fin de la lista, guardar al final del último cluster del directorio')
                        cluster_inicial = ed_actual.cluster_inicial + clusters_usados # Cluster inicial + Clusters usados por éste 
                        clusters_libres = self.clusters_totales - cluster_inicial
            
            # Vemos si queda espacio para guardar el archivo
            if clusters_requeridos > clusters_libres:
                print('No hay espacio en la unidad para guardar el archivo')
                return False

            # Guardamos el archivo a partir del cluster "cluster_inicial"
            print('Guardando "%s" en cluster %i' % (origen, cluster_inicial))
            ed_nueva = EntradaDir(destino, tam_archivo, cluster_inicial, now(), now())
            return self.agregarEntDir(ed_nueva, bytes_archivo)

        except IOError as ioerr:
            print('IOError: %s' % ioerr)
            return False
    
    def eliminar(self, archivo, harddel = False):
        """Eliminar un archivo de FIUNAMFS
        Atributos:
            archivo -- nombre del archivo a eliminar
            harddel -- booleano que indica si se hará un borrado 'suave' o 'duro'.\
            El borrado suave, sólo marca la entrada del directorio con la cadena de 'desocupado'.\
            En el borrado duro, borra los datos de la entrada del directorio y los datos del archivo
        """
        if not self.montado:
            print(MSGERR_NO_MONTADO)
            return False

        resultado = list(filter( lambda entdir: entdir.nombre == archivo, self.__listaEntDir)) # Buscamos el elemento que coincida
        if not resultado:
            print(MSGERR_ARCH_NO_ENC)
            return False

        #nuevaListaEntDir = list(set(self.__listaEntDir) - set(resultado)) # Le restamos el valor que encontramos
        #print(nuevaListaEntDir)

        entrDir = resultado.pop() # Obtenemos la entrada del directorio
        
        self.__listaEntDir.remove(entrDir)
        print(self.__listaEntDir)

        self.__mmfs[entrDir.direccion_ed : entrDir.direccion_ed + 15] = STR_DIR_VACIO.encode('ascii') # Marcamos el directorio como disponible
        
        if harddel:
            self.__mmfs[entrDir.direccion_ed : entrDir.direccion_ed + 64] = ('\0'*64).encode('ascii') # Borramos la entrada del directorio

            dir_inicio = entrDir.cluster_inicial * self.tam_cluster # dirección de inicio
            dir_fin = dir_inicio + entrDir.tam_archivo # dirección de fin
            self.__mmfs[dir_inicio : dir_fin] = ('\0'*entrDir.tam_archivo).encode('ascii') # Borramos sus datos
        
        print('%s borrado exitosamente.' % archivo)
        return True

    
    def agregarEntDir(self, entDir, datos):
        """Agrega una EntradaDir al directorio de FIUNAMFS
        Atributos:
            entDir -- EntradaDir a agregar
            datos -- los datos del archivo a escribir
        Retorna:
            Valor booleano que marca True si logró agregar la entrada y false en caso contrario
        """
        if not self.montado:
            print(MSGERR_NO_MONTADO)
            return False
        
        inicio = self.tam_cluster
        fin = self.tam_dir+self.tam_cluster
        paso = self.tam_entradadir
        for i in range(inicio,fin,paso):
            nombre_ant = self.__mmfs[i + 0 : i + 15].decode('ascii')
            if nombre_ant == STR_DIR_VACIO: # Comparamos lo que hay en el nombre con la cadena de entrada de dir vacía
                
                self.__mmfs[i + 0 : i + 15] = ('%15s' % entDir.nombre).encode('ascii')
                self.__mmfs[i + 16 : i + 24] = ('%08s' % entDir.tam_archivo).encode('ascii')
                self.__mmfs[i + 25 : i + 30] = ('%05s' % entDir.cluster_inicial).encode('ascii')
                self.__mmfs[i + 31 : i + 45] = ('%14s' % entDir.f_creacion).encode('ascii')
                self.__mmfs[i + 46 : i + 60] = ('%14s' % entDir.f_modif).encode('ascii')

                dir_inicio_datos = entDir.cluster_inicial*self.tam_cluster
                tam_archivo = len(datos)

                # print('Tamaño mmap fs: ', len(self.__mmfs[dir_inicio_datos : dir_inicio_datos + tam_archivo]))
                # print('Tamaño a escribir: ', len(datos))
                
                self.__mmfs[dir_inicio_datos : dir_inicio_datos+tam_archivo]=datos
                
                self.__mmfs.flush()
                
                entDir.direccion_ed = i # Le indicamos en qué dirección inicia la entrada del directorio
                print(entDir.direccion_ed)
                self.__listaEntDir.append(entDir) # Agregamos la entrada a la lista
                return True
    
    def formatear(self, version=0.8,
                label='No Label', sector_size=512, sect_per_clust=4,
                dir_clusters=4):
        pass
    
    def guardarimg(self, filename):
        pass

    @staticmethod
    def crearimg(filename, version=0.8,
                label='No Label', sector_size=512, sect_per_clust=4,
                dir_clusters=4, tot_clusters=720):
        """Tomé prestado el método init de su programa y lo hice un método estático
        """
        fsname = NOMBRE_FS

        direntry_size = 64
        cluster_size = sector_size * sect_per_clust
        tot_direntries = int(cluster_size * dir_clusters /
                                  direntry_size)
        total_size = cluster_size * tot_clusters

        if not os.path.isfile(filename):
            # Para dimensionar al sistema del tamaño deseado, creamos
            # un archivo vacío, saltamos (seek()) hasta el punto
            # máximo menos un byte, y escribimos un byte (\0). Todo el
            # espacio restante se llena de \0.
            with open(filename, 'w') as out:
                out.seek(tot_clusters * cluster_size - 1)
                out.write("\0")
        
        filesize = os.stat(filename).st_size
        if filesize != total_size:
            raise RuntimeError(('El archivo %s existe, pero es de tamaño ' +
                                'incorrecto (%d != %d)') %
                               (filename, total_size, filesize))

        fh = open(filename, 'r+')
        data = mmap(fh.fileno(), 0)

        # Inicializa el "superbloque" (el primer sector) del sistema de archivos
        print('Inicializando volumen %s versión %s, etiqueta «%s»' %
              (fsname, version, label))
        print('Tamaño de cluster: %d. Tamaño de directorio: %d clusters' %
              (cluster_size, direntry_size))
        print('Entradas de directorio: %d. Clusters totales: %d' %
              (tot_direntries, tot_clusters))

        data[0:8] = ('%8s' % NOMBRE_FS).encode()
        data[10:13] = ('%3s' % version).encode()
        data[20:35] = ('%15s' % label).encode()
        data[40:45] = ('%05d' % cluster_size).encode()
        data[47:49] = ('%02d' % dir_clusters).encode()
        data[52:60] = ('%08d' % tot_clusters).encode()

        for i in range(tot_direntries):
            inicio = cluster_size
            fin = cluster_size*dir_clusters+cluster_size
            paso = direntry_size
            for j in range(inicio,fin,paso):                  
                data[j + 0 : j + 15] = ('%15s' % STR_DIR_VACIO).encode('ascii')            
                data.flush()
        data.close()
        fh.close()
        return True

class EntradaDir(object):
    def __init__(self, nombre, tam_archivo, cluster_inicial, f_creacion = now(), f_modif = now(), direccion_ed = 0):
        self.nombre = nombre
        self.tam_archivo = tam_archivo
        self.cluster_inicial = cluster_inicial
        self.f_creacion = f_creacion
        self.f_modif = f_modif
        self.direccion_ed = direccion_ed

    def __str__(self):
        return '%i %s %i bytes %s %s' % (self.tam_archivo, 
                                    self.nombre, 
                                    self.cluster_inicial, 
                                    self.f_creacion, 
                                    self.f_modif)
    
    def __eq__(self, value):
        return self.nombre == value.nombre and self.cluster_inicial == value.cluster_inicial

# Error de sistema no montado
# class NMError(Error):
#     def __init__(self, expression, message):
#         self.expression = expression
#         self.message = message