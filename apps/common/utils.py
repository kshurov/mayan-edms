# -*- coding: iso-8859-1 -*-
import os
import re
import types

from django.utils.http import urlquote  as django_urlquote
from django.utils.http import urlencode as django_urlencode
from django.utils.datastructures import MultiValueDict
from django.conf import settings


def urlquote(link=None, get={}):
    u'''
    This method does both: urlquote() and urlencode()

    urlqoute(): Quote special characters in 'link'

    urlencode(): Map dictionary to query string key=value&...

    HTML escaping is not done.

    Example:

      urlquote('/wiki/Python_(programming_language)')     --> '/wiki/Python_%28programming_language%29'
      urlquote('/mypath/', {'key': 'value'})              --> '/mypath/?key=value'
      urlquote('/mypath/', {'key': ['value1', 'value2']}) --> '/mypath/?key=value1&key=value2'
      urlquote({'key': ['value1', 'value2']})             --> 'key=value1&key=value2'
    '''
    assert link or get
    if isinstance(link, dict):
        # urlqoute({'key': 'value', 'key2': 'value2'}) --> key=value&key2=value2
        assert not get, get
        get = link
        link = ''
    assert isinstance(get, dict), 'wrong type "%s", dict required' % type(get)
    #assert not (link.startswith('http://') or link.startswith('https://')), \
    #    'This method should only quote the url path. 
    #    It should not start with http(s)://  (%s)' % (
    #    link)
    if get:
        # http://code.djangoproject.com/ticket/9089
        if isinstance(get, MultiValueDict):
            get = get.lists()
        if link:
            link = '%s?' % django_urlquote(link)
        return u'%s%s' % (link, django_urlencode(get, doseq=True))
    else:
        return django_urlquote(link)


def return_attrib(obj, attrib, arguments={}):
    try:
        if isinstance(attrib, types.FunctionType):
            return attrib(obj)
        elif isinstance(obj, types.DictType) or isinstance(obj, types.DictionaryType):
            return obj[attrib]
        else:
            result = reduce(getattr, attrib.split('.'), obj)
            if isinstance(result, types.MethodType):
                if arguments:
                    return result(**arguments)
                else:
                    return result()
            else:
                return result
    except Exception, err:
        if settings.DEBUG:
            return 'Attribute error: %s; %s' % (attrib, err)
        else:
            pass


#http://snippets.dzone.com/posts/show/5434
#http://snippets.dzone.com/user/jakob
def pretty_size(size, suffixes = [('B', 2**10), ('K', 2**20), ('M', 2**30), ('G', 2**40), ('T', 2**50)]):
    for suf, lim in suffixes:
        if size > lim:
            continue
        else:
            return round(size/float(lim/2**10), 2).__str__()+suf

def pretty_size_10(size):
    return pretty_size(size, suffixes = [('B', 10**3), ('K', 10**6), ('M', 10**9), ('G', 10**12), ('T', 10**15)])


def exists_with_famfam(path):
    try:
        if os.path.exists(path):
            return '<span class="famfam active famfam-tick"></span>'
        else:
            return '<span class="famfam active famfam-cross"></span>'
    except Exception, exc:
        return exc


# The code here is based loosely on John Cardinal's notes found at:
# http://www.johncardinal.com/tmgutil/capitalizenames.htm

# 2006-03-16
# Thanks to David Kern <kernd@reasonspace.com> for fixing some bugs.

#class Name(str):
#    """A Class (based on the string type) that properly capitalizes a name."""
#
#    def __new__(cls, value=''):
#        original = value
#        proper = Capitalize(value)
#        obj = str.__new__(cls, proper)
#        obj.original = original
#        return obj

def proper_name(name):
    """Does the work of capitalizing a name (can be a full name)."""

    suffixes = [
        u"II", u"(II)", u"III", u"(III)", u"IV", u"(IV)", u"VI", u"(VI)", 
        u"VII", u"(VII)", u"2nd", u"(2nd)", u"3rd", u"(3rd)", u"4th", u"(4th)", 
        u"5th", u"(5th)"
    ]

    # The names listed here are included by permission from John Cardinal's TMG Utility.
    # http://www.johncardinal.com/tmgutil/index.htm
    # John Cardinal maintains the copyright for this list of names.
    surnames = [
        u"ApShaw", u"d'Albini", "d'Aubigney", u"d'Aubigné", u"d'Autry", 
        u"d'Entremont", u"d'Hurst", u"D'ovidio", u"da Graça", u"DaSilva",
        u"DeAnda", u"deAnnethe", u"deAubigne", u"deAubigny", u"DeBardelaben",
        u"DeBardeleben", u"DeBaugh", u"deBeauford", u"DeBerry", u"deBethune",
        u"DeBetuile", u"DeBoard", u"DeBoer", u"DeBohun", u"DeBord", u"DeBose",
        u"DeBrouwer", u"DeBroux", u"DeBruhl", u"deBruijn", u"deBrus", u"deBruse", 
        u"deBrusse", u"DeBruyne", u"DeBusk", u"DeCamp", u"deCastilla", u"DeCello",
        u"deClare", u"DeClark", u"DeClerck", u"DeCoste", u"deCote", u"DeCoudres", 
        u"DeCoursey", u"DeCredico", u"deCuire", u"DeCuyre", u"DeDominicios", 
        u"DeDuyster", u"DeDuytscher", u"DeDuytser", u"deFiennes", u"DeFord", 
        u"DeForest", u"DeFrance", u"DeFriece", u"DeGarmo", u"deGraaff", u"DeGraff", 
        u"DeGraffenreid", u"DeGraw", u"DeGrenier", u"DeGroats", u"DeGroft", 
        u"DeGrote", u"DeHaan", u"DeHaas", u"DeHaddeclive", u"deHannethe", 
        u"DeHatclyf", u"DeHaven", u"DeHeer", u"DeJager", u"DeJarnette", u"DeJean", 
        u"DeJong", u"deJonge", u"deKemmeter", u"deKirketon", u"DeKroon", 
        u"deKype", u"del-Rosario", u"dela Chamotte", u"DeLa Cuadra", 
        u"DeLa Force", u"dela Fountaine", u"dela Greña", u"dela Place", 
        u"DeLa Ward", u"DeLaci", u"DeLacy", u"DeLaet", u"DeLalonde", u"DelAmarre", 
        u"DeLancey", u"DeLascy", u"DelAshmutt", u"DeLassy", u"DeLattre", 
        u"DeLaughter", u"DeLay", u"deLessine", u"DelGado", u"DelGaudio", 
        u"DeLiberti", u"DeLoache", u"DeLoatch", u"DeLoch", u"DeLockwood", 
        u"DeLong", u"DeLozier", u"DeLuca", u"DeLucenay", u"deLucy", u"DeMars", 
        u"DeMartino", u"deMaule", u"DeMello", u"DeMinck", u"DeMink", u"DeMoree", 
        u"DeMoss", u"DeMott", u"DeMuynck", u"deNiet", u"DeNise", u"DeNure", 
        u"DePalma", u"DePasquale", u"dePender", u"dePercy", u"DePoe", u"DePriest", 
        u"DePu", u"DePui", u"DePuis", u"DeReeper", u"deRochette", u"deRose", 
        u"DeRossett", u"DeRover", u"deRuggele", u"deRuggle", u"DeRuyter", 
        u"deSaint-Sauveur", u"DeSantis", u"desCuirs", u"DeSentis", u"DeShane", 
        u"DeSilva", u"DesJardins", u"DesMarest", u"deSoleure", u"DeSoto", 
        u"DeSpain", u"DeStefano", u"deSwaert", u"deSwart", u"DeVall", u"DeVane", 
        u"DeVasher", u"DeVasier", u"DeVaughan", u"DeVaughn", u"DeVault", u"DeVeau", 
        u"DeVeault", u"deVilleneuve", u"DeVilliers", u"DeVinney", u"DeVito", 
        u"deVogel", u"DeVolder", u"DeVolld", u"DeVore", u"deVos", u"DeVries", 
        u"deVries", u"DeWall", u"DeWaller", u"DeWalt", u"deWashington", 
        u"deWerly", u"deWessyngton", u"DeWet", u"deWinter", u"DeWitt", u"DeWolf", 
        u"DeWolfe", u"DeWolff", u"DeWoody", u"DeYager", u"DeYarmett", u"DeYoung", 
        u"DiCicco", u"DiCredico", u"DiFillippi", u"DiGiacomo", u"DiMarco", 
        u"DiMeo", u"DiMonte", u"DiNonno", u"DiPietro", u"diPilato", u"DiPrima", 
        u"DiSalvo", u"du Bosc", u"du Hurst", u"DuFort", u"DuMars", u"DuPre", 
        u"DuPue", u"DuPuy", u"FitzUryan", u"kummel", u"LaBarge", u"LaBarr", 
        u"LaBauve", u"LaBean", u"LaBelle", u"LaBerteaux", u"LaBine", u"LaBonte", 
        u"LaBorde", u"LaBounty", u"LaBranche", u"LaBrash", u"LaCaille", u"LaCasse", 
        u"LaChapelle", u"LaClair", u"LaComb", u"LaCoste", u"LaCount", u"LaCour", 
        u"LaCroix", u"LaFarlett", u"LaFarlette", u"LaFerry", u"LaFlamme", 
        u"LaFollette", u"LaForge", u"LaFortune", u"LaFoy", u"LaFramboise", 
        u"LaFrance", u"LaFuze", u"LaGioia", u"LaGrone", u"LaLiberte", u"LaLonde", 
        u"LaLone", u"LaMaster", u"LaMay", u"LaMere", u"LaMont", u"LaMotte", 
        u"LaPeer", u"LaPierre", u"LaPlante", u"LaPoint", u"LaPointe", u"LaPorte", 
        u"LaPrade", u"LaRocca", u"LaRochelle", u"LaRose", u"LaRue", u"LaVallee", 
        u"LaVaque", u"LaVeau", u"LeBleu", u"LeBoeuf", u"LeBoiteaux", u"LeBoyteulx", 
        u"LeCheminant", u"LeClair", u"LeClerc", u"LeCompte", u"LeCroy", u"LeDuc", 
        u"LeFevbre", u"LeFever", u"LeFevre", u"LeFlore", u"LeGette", u"LeGrand", 
        u"LeGrave", u"LeGro", u"LeGros", u"LeJeune", u"LeMaistre", u"LeMaitre", 
        u"LeMaster", u"LeMesurier", u"LeMieux", u"LeMoe", u"LeMoigne", u"LeMoine", 
        u"LeNeve", u"LePage", u"LeQuire", u"LeQuyer", u"LeRou", u"LeRoy", u"LeSuer", 
        u"LeSueur", u"LeTardif", u"LeVally", u"LeVert", u"LoMonaco", u"Macabe", 
        u"Macaluso", u"MacaTasney", u"Macaulay", u"Macchitelli", u"Maccoone", 
        u"Maccurry", u"Macdermattroe", u"Macdiarmada", u"Macelvaine", u"Macey", 
        u"Macgraugh", u"Machan", u"Machann", u"Machum", u"Maciejewski", u"Maciel", 
        u"Mackaben", u"Mackall", u"Mackartee", u"Mackay", u"Macken", u"Mackert", 
        u"Mackey", u"Mackie", u"Mackin", u"Mackins", u"Macklin", u"Macko", 
        u"Macksey", u"Mackwilliams", u"Maclean", u"Maclinden", u"Macomb", 
        u"Macomber", u"Macon", u"Macoombs", u"Macraw", u"Macumber", u"Macurdy", 
        u"Macwilliams", u"MaGuinness", u"MakCubyn", u"MakCumby", u"Mcelvany", 
        u"Mcsherry", u"Op den Dyck", u"Op den Graeff", u"regory", u"Schweißguth", 
        u"StElmo", u"StGelais", u"StJacques", u"te Boveldt", u"VanAernam", 
        u"VanAken", u"VanAlstine", u"VanAmersfoort", u"VanAntwerp", u"VanArlem", 
        u"VanArnam", u"VanArnem", u"VanArnhem", u"VanArnon", u"VanArsdale", 
        u"VanArsdalen", u"VanArsdol", u"vanAssema", u"vanAsten", u"VanAuken", 
        u"VanAwman", u"VanBaucom", u"VanBebber", u"VanBeber", u"VanBenschoten", 
        u"VanBibber", u"VanBilliard", u"vanBlare", u"vanBlaricom", u"VanBuren", 
        u"VanBuskirk", u"VanCamp", u"VanCampen", u"VanCleave", u"VanCleef", 
        u"VanCleve", u"VanCouwenhoven", u"VanCovenhoven", u"VanCowenhoven", 
        u"VanCuren", u"VanDalsem", u"VanDam", u"VanDe Poel", u"vanden Dijkgraaf", 
        u"vanden Kommer", u"VanDer Aar", u"vander Gouwe", u"VanDer Honing", 
        u"VanDer Hooning", u"vander Horst", u"vander Kroft", u"vander Krogt", 
        u"VanDer Meer", u"vander Meulen", u"vander Putte", u"vander Schooren", 
        u"VanDer Veen", u"VanDer Ven", u"VanDer Wal", u"VanDer Weide", 
        u"VanDer Willigen", u"vander Wulp", u"vander Zanden", u"vander Zwan", 
        u"VanDer Zweep", u"VanDeren", u"VanDerlaan", u"VanDerveer", 
        u"VanderWoude", u"VanDeursen", u"VanDeusen", u"vanDijk", u"VanDoren", 
        u"VanDorn", u"VanDort", u"VanDruff", u"VanDryer", u"VanDusen", u"VanDuzee", 
        u"VanDuzen", u"VanDuzer", u"VanDyck", u"VanDyke", u"VanEman", u"VanEmmen", 
        u"vanEmmerik", u"VanEngen", u"vanErp", u"vanEssen", u"VanFleet", 
        u"VanGalder", u"VanGelder", u"vanGerrevink", u"VanGog", u"vanGogh", 
        u"VanGorder", u"VanGordon", u"VanGroningen", u"VanGuilder", u"VanGundy", 
        u"VanHaaften", u"VanHaute", u"VanHees", u"vanHeugten", u"VanHise", 
        u"VanHoeck", u"VanHoek", u"VanHook", u"vanHoorn", u"VanHoornbeeck", 
        u"VanHoose", u"VanHooser", u"VanHorn", u"VanHorne", u"VanHouten", 
        u"VanHoye", u"VanHuijstee", u"VanHuss", u"VanImmon", u"VanKersschaever", 
        u"VanKeuren", u"VanKleeck", u"VanKoughnet", u"VanKouwenhoven", 
        u"VanKuykendaal", u"vanLeeuwen", u"vanLent", u"vanLet", u"VanLeuven", 
        u"vanLingen", u"VanLoozen", u"VanLopik", u"VanLuven", u"vanMaasdijk", 
        u"VanMele", u"VanMeter", u"vanMoorsel", u"VanMoorst", u"VanMossevelde", 
        u"VanNaarden", u"VanNamen", u"VanNemon", u"VanNess", u"VanNest", 
        u"VanNimmen", u"vanNobelen", u"VanNorman", u"VanNormon", u"VanNostrunt", 
        u"VanNote", u"VanOker", u"vanOosten", u"VanOrden", u"VanOrder", 
        u"VanOrma", u"VanOrman", u"VanOrnum", u"VanOstrander", u"VanOvermeire", 
        u"VanPelt", u"VanPool", u"VanPoole", u"VanPoorvliet", u"VanPutten", 
        u"vanRee", u"VanRhijn", u"vanRijswijk", u"VanRotmer", u"VanSchaick", 
        u"vanSchelt", u"VanSchoik", u"VanSchoonhoven", u"VanSciver", u"VanScoy", 
        u"VanScoyoc", u"vanSeters", u"VanSickle", u"VanSky", u"VanSnellenberg", 
        u"vanStaveren", u"VanStraten", u"VanSuijdam", u"VanTassel", u"VanTassell", 
        u"VanTessel", u"VanTexel", u"VanTuyl", u"VanValckenburgh", u"vanValen", 
        u"VanValkenburg", u"VanVelsor", u"VanVelzor", u"VanVlack", u"VanVleck", 
        u"VanVleckeren", u"VanWaard", u"VanWart", u"VanWassenhove", u"VanWinkle", 
        u"VanWoggelum", u"vanWordragen", u"VanWormer", u"VanZuidam", 
        u"VanZuijdam", u"VonAdenbach", u"vonAllmen", u"vonBardeleben", 
        u"vonBerckefeldt", u"VonBergen", u"vonBreyman", u"VonCannon", 
        u"vonFreymann", u"vonHeimburg", u"VonHuben", u"vonKramer", 
        u"vonKruchenburg", u"vonPostel", u"VonRohr", u"VonRohrbach", 
        u"VonSass", u"VonSasse", u"vonSchlotte", u"VonSchneider", u"VonSeldern", 
        u"VonSpringer", u"VonVeyelmann", u"VonZweidorff"
    ]
       
    hyphen_indexes = []
    while name.find('-') > -1:
        index = name.find('-')
        hyphen_indexes.append(index)
        name = name[:index] + ' ' + name[index+1:]
    name = name.split()
    name = [w.capitalize() for w in name] # standard capitalization
    # "Mcx" should be "McX"
    index = 0
    for w in name:
        try:
            name[index] = mc.sub("Mc"+w[2].upper(), w)
        except:
            pass
        index += 1
    # "Macx" should be "MacX"
    index = 0
    for w in name:
        try:
            name[index] = mac.sub("Mac"+w[3].upper(), w)
        except:
            pass
        index += 1
    name = ' '.join( name )
    for index in hyphen_indexes:
        name = name[:index] + '-' + name[index+1:]
    
    # funky stuff (no capitalization)
    name = name.replace(" Dit ", " dit ")
    name = name.replace(" Van ", " van ")
    name = name.replace(" De ", " de ")
    
    # special surnames and suffixes
    name += ' '
    for surname in surnames + suffixes:
        pos = name.lower().find(surname.lower())
        if pos > -1:
            # surname/suffix must be:
            # 1. at start of name or after a space
            #          -and-
            # 2. followed by the end of string or a space
            if (((pos == 0) or (pos > 0 and name[pos-1] == ' '))
                and ((len(name) == pos+len(surname))
                or (name[pos+len(surname)] == ' '))):
                name = name[:pos] + surname + name[pos+len(surname):]
    return name.strip()
    
mc = re.compile(r"^Mc(\w)(?=\w)", re.I)
mac = re.compile(r"^Mac(\w)(?=\w)", re.I)
