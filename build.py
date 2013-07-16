# coding:utf-8
import codecs
import os
import re
from os.path import getsize, splitext
import json
import shutil

luaDir = "tolua++"
snippetsDir = "snippets"
templatePath = "template.sublime-snippet"
completionTemplatePath = "template_completions.sublime-completions"


template = codecs.open(templatePath, "r", "utf-8").read()
templateCompletion = codecs.open(completionTemplatePath, "r", "utf-8").read()
data = {}
dictStr = []

def cleanDir( Dir ):
    print("cleanDir:", Dir)
    if os.path.isdir( Dir ):
        paths = os.listdir( Dir )
        for path in paths:
            filePath = os.path.join( Dir, path )
            if os.path.isfile( filePath ):
                try:
                    os.remove( filePath )
                except os.error:
                    autoRun.exception( "remove %s error." %filePath )#引入logging
            elif os.path.isdir( filePath ):
                print("clean", filePath)
                shutil.rmtree(filePath,True)
    return True

os.makedirs(snippetsDir, exist_ok=True)
cleanDir(snippetsDir)

#                     class    AAA    :       {func }
klassP =  re.compile('class\s+(\w+)\s*:?\s*(.*?)\s*{(.*?)}', re.S)

#                   void       func(  int a, int b)
funcP = re.compile('\w+[\s\*&]+(\w+)\((.*?)\)', re.S)
funcSP = re.compile('\s+static\s+\w+[\s\*&]+(\w+)\((.*?)\)', re.S)

#                   typedef enum {}typename;
enumP = re.compile('\s*enum[\s\S]*?{([\s\S]*?)}', re.S)
enumItem = re.compile('\s+([_a-zA-Z][_a-zA-Z0-9]*)', re.S)

def outDict():
    tpl = templateCompletion
    contentStr = ""
    for str in dictStr:
        contentStr = contentStr + '\t\t"' + str + '"' + ",\n"
    tpl = tpl.replace("%content",contentStr)
    ff = codecs.open(os.path.join(snippetsDir, "enum.sublime-completions"), "w", "utf-8")
    ff.write(tpl)
    ff.close()

def outPut(klass, func, args, is_static):
    #print("write:", klass,func)
    tpl = template
    if is_static == False:
        tpl = template.replace("%class:", "")    
    tpl = tpl.replace("%class", klass)
    tpl = tpl.replace("%func", func)
    argList = args.split(",")
    args = ""
    i = 1
    if len(argList)==0 or argList[0]=="void":
        args = ""
    else:
        for arg in argList:
            args += "${" + str(i) + ":" + arg + "}" + ","
            i+=1
        args = args[:-1]
    tpl = tpl.replace("%args", args)
    tempDir = os.path.join(snippetsDir, klass)
    os.makedirs(tempDir, exist_ok=True)
    ff = codecs.open(os.path.join(tempDir, klass+"_"+func)+".sublime-snippet", "w", "utf-8")
    ff.write(tpl)
    ff.close()

def getSuperKlass(str):
    if str == "":
        return []
    else:
        return re.sub(r"\s*public\s*", "", str).split(",")

def getData(file):
    text = codecs.open(file, "r", "utf-8").read()
    text = re.sub(r"/\*[\S\s]*?\*/", "", text)
    text = re.sub(r"//[^\t\n]*", "", text)

    enumDefs = enumP.findall(text)
    for enumDef in enumDefs:
        #print(enumStrs)
        enumStrs = enumItem.findall(enumDef)
        for enumStr in enumStrs:
            #print(enumStr)
            if (enumStr in dictStr) == False:
                dictStr.append(enumStr)

    klasses = klassP.findall(text)
    for klass in klasses:
        klassData = {}
        superKlass = ""
        if len(klass) == 2:
            klassName = klass[0]
            funcStr = klass[1]
        else:
            klassName = klass[0]
            superKlass = klass[1]
            funcStr = klass[2]
        klassData["klass"] = klassName
        klassData["super"] = getSuperKlass(superKlass)

        staticFuncData = klassData["static_func"] = {}
        funcs = funcSP.findall(funcStr)
        for func in funcs:
            funcName = func[0]
            args = re.sub(r",[\n\r\s]+", ",", func[1])
            args = re.sub(r"\s+", "_", args)
            staticFuncData[funcName] = args
        funcStr = funcSP.sub("",funcStr)

        funcData = klassData["func"] = {}
        funcs = funcP.findall(funcStr)
        for func in funcs:
            funcName = func[0]
            args = re.sub(r",[\n\r\s]+", ",", func[1])
            args = re.sub(r"\s+", "_", args)
            funcData[funcName] = args
        data[klassName] = klassData

for file in os.listdir(luaDir):
    #if(splitext(file)[1]==".pkg" and splitext(file)[0]=="CCApplication"):
    if(splitext(file)[1]==".pkg"):
        getData(os.path.join(luaDir, file))


tree = {}

    
def extends(childKlassData, superKlass):
    if superKlass not in data:
        tree[superKlass] = {
            "klass":superKlass,
            "func":"",
            "super":[]
        }
    if superKlass not in tree and len(data[superKlass]["super"]) == 0:
        tree[superKlass] = data[superKlass]
    if superKlass in tree:
        for func in tree[superKlass]["func"]:
            childKlassData["func"][func] = tree[superKlass]["func"][func]
    else:
        for func in data[superKlass]["func"]:
            childKlassData["func"][func] = data[superKlass]["func"][func]
            for superName in data[superKlass]["super"]:
                extends(childKlassData, superName)
    tree[childKlassData["klass"]] = childKlassData


for klass in data:
    #print("________________________", klass, "___________________")
    if len(data[klass]["super"]) == 0:
        tree[klass] = data[klass]
    else:
        for superName in data[klass]["super"]:
            #print(superName)
            extends(data[klass], superName)


for klass in tree:
    #print(klass+":")
    for func in tree[klass]["func"]:
        outPut(klass, func, tree[klass]["func"][func], False)
    if "static_func" in tree[klass]:
        for func in tree[klass]["static_func"]:
            outPut(klass, func, tree[klass]["static_func"][func], True)


outDict()


if os.name == "nt":
    os.system("pause")