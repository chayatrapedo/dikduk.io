"""
Chaya Trapedo - dkdk.io Transliteration Editor
I hereby certify that this program is solely the result of my own work and 
is in compliance with the Academic Integrity policy of the course syllabus. 

NOTE: Full citations to external resources are in "Project Info.txt"
"""
import Draw
import string
from intro_typing import intro, validKeys_letNums, validKeys_other

# All constant variables:

# Constants for rendered window
CANVAS_WIDTH, CANVAS_HEIGHT = 1100, 825

# Constants for spacing rendered words 
HORIZ_WORD_SPACE, VERT_WORD_SPACE, PARAGRAPH_SPACING = 6, 8, 15

# Threshold for minumum edit dist for a word to be flagged
DIST_THRESH = 2

# all punctuation in text files
ALL_PUNCT = string.punctuation + "“" + "”" + "—" + "’"

# stores all Word object nessecary information for rendered words and functions 
# that access / mutate indivial word objects, the entire Word class, or word-related
# variables (translitwords list, English words list, number of edits, etc.)
class Word(object):
    
    # class vairables:
    
    # lists in word class for lists of strings (English/Translit words) or lists
    # of word objects
    __TranslitWords = []
    __EngWords = [ ]
    
    #list of words rendered in page bounds
    __RenderList = [ ]
    
    #tracks amount of edits made by user
    __TotalEdits = 0
    
    # static methods:
    # relating to __TranslitWords/__EngWords:
    
    # imports correctly spelled transliterated strings for edit distance comparisons
    # and stores them in __TranslitWords (Couresty of SIE)
    @staticmethod
    def importtranslit():
        
        translit = open("TranslitWords.csv")
        
        # [:-1] to read until up to and not "\n" from every line
        Word.__TranslitWords = [w[:-1] for w in translit]  
        translit.close()
    
    # imports ~1200 most common English words, numbers, and Roman numerals
    # and stores them to __EngWords = [ ] (courtesy of Princeton Intro to CS)
    @staticmethod
    def importenglish():
        englishwords = open("mostcommonwordsandnums.txt")
        Word.__EngWords = [w.strip() for w in englishwords]
        englishwords.close()
    
    # relating to __RenderList:
    
    # determines which words are clickable on each rendered page based on flagging
    # returns list of clickable words
    @staticmethod 
    def clickableWords(pageList):

        # fencepost problem where first page (i.e. pagelist = [0, next page] 
        # determines clickability differently from other pages
        if len(pageList) == 2: wordsOnPage = Word.__RenderList[pageList[-2]:pageList[-1]]
        else: wordsOnPage = Word.__RenderList[pageList[-1]:]
        
        # return a list of flagged words
        return [word for word in wordsOnPage if word.flagged()]

    # when the "<" back button is pressed, the list of rendered words
    # is truncated to "delete" current page 
    @staticmethod
    def backPage(pageList):  
        Word.__RenderList = Word.__RenderList[:pageList[-2]]
         
        
    # relating to __TotalEdits:
    
    # increments total when a change is made
    @staticmethod
    def editMade():
        Word.__TotalEdits += 1
    
    # getting method   
    @staticmethod
    def TotalEdits():
        return Word.__TotalEdits    
        
    # Word object methods:

    # initializes a new word
    def __init__(self, string, wordindex=None):
        self.__text = string  # text of word
        self.__wordindex = wordindex  # number word that it is for later matching in list

        # Initialized 4 location variables, which are set in draw()
        # upper-left corner x , # upper-left corner y coordinate, width and height
        self.__x = self.__y = self.__w = self.__h = None  
        
        # Editability variables that store minimum edit distance, whether a word
        # is flagged to be editable, and top 3 closest replacements, which are 
        # set in editability()
        self.__minDist = self.__flag = self.__top3 = None

        self.editability()
    
       
    # determine edit distance and 3 closest words for each initialized word
    # sets initialized values that determine the editiability of each word
    def editability(self):
        
        # stores the 3 closest edit-dist derived matchtes        
        top3 = [ ]
        
        # if the word is just punctuation, set "empty" values
        if self.__text in ALL_PUNCT: 
            dist = 0
            flag = False
        
        else: # analyze words without leading/trailing punctuation
            testWord = stripPunct(self.__text)
            
            # if the word is in the transliterated/English words list, then it's
            # not mispelled and fine
            if testWord in Word.__TranslitWords or testWord.lower() in Word.__EngWords:
                dist = 0
                flag = False
                
            else: # find closest translit. words because it's probably mispelled
                
                # determine mininum edit distance, starting "dist" is length of word
                minDist = len(self.__text)
        
                closestWord = ""
                for w in Word.__TranslitWords:
                    # find edit of self compared to all words in TranslitWords
                    curDist = self.editDistFormula(w)
                  
                    # store smallest value
                    if curDist <= minDist: # and curDist <= DIST_THRESH:
                        minDist = curDist
                        closestWord = w
                        top3.append(w)
                            
                self.__top3 = top3[-3:]
                self.__top3.reverse()
                self.__dist = minDist
        
                # if edit dist < threshold and it's not a word that exists, it 
                # should be clickable
                self.__flag = self.__dist <= DIST_THRESH and self.__dist > 0  

    # Finds the edit distance between two strings (self, another word) and
    # returns an int of distance (courtesy of Machine Learning Knowledge)
    def editDistFormula(self, otherWord): 
         
        # strip punctuation for comparison purposes
        strip = stripPunct(self.__text)
        
        # edit distance formula
        lSelf = len(strip)
        lOther = len(otherWord)
        d = [[0] * (lOther + 1) for i in range(lSelf + 1)]

        for i in range(1, lSelf + 1): d[i][0] = i

        for j in range(1, lOther + 1): d[0][j] = j

        for j in range(1, lOther + 1):
            for i in range(1, lSelf + 1):
                if strip[i - 1] == otherWord[j - 1]: cost = 0
                else: cost = 1

                d[i][j] = min(d[i - 1][j] + 1,  # deletion
                              d[i][j - 1] + 1,  # insertion
                              d[i - 1][j - 1] + cost) #substitution
                
        return d[lSelf][lOther] # edit distance
    

    # renders the words in the given position -  used for determining word 
    # location before rendering in canvas bounds, and rendering word on "paper"
    # each word is rendered twice - 1) offscreen at the correct x position but
    # offset 
    def render(self, x, y, size):

        # assigns a list of positions x1, y,1, x2, y2
        Draw.setFontSize(size)

        # if the word is flagged for being potentially mispelled, it is rendered
        # in red and bolded
        if self.__flag:
            Draw.setColor(Draw.RED)
            Draw.setFontBold(True)
        else:
            Draw.setColor(Draw.BLACK)
            Draw.setFontBold(False)

        # Draw word, disable bold
        word = Draw.string(self.__text, x, y)
        Draw.setFontBold(False)
        
        self.__w = word[2] - word[0]
        self.__h = word[3] - word[1]
        self.__x = word[0]
        
        # if the word is rendered on the page (not at -500), set the y value of 
        # word
        if y != -500: 
            self.__y = word[1]
        
                                # x1,       x2,      y1,      y2
        self.__locationStats = [word[0], word[2], word[1], word[3]]
        return self.__locationStats

    # check if x, y values are within the bounds of the word
    def clicked(self, clickX, clickY):
        if clickX > self.__x and clickX < self.__x + self.__w and \
           clickY > self.__y and clickY < self.__y + self.__h:
            return True
        return False
    
    # add word to list of rendered words, called when rendered not at y = -500
    def toRenderList(self):
        Word.__RenderList.append(self)
        
    # When "add to dictionary" is clicked, word is added to "dictionary"/list 
    # of Translit words, will not be flagged as incorrect again, and will be 
    # suggested as an alternative word from TranslitWords
    def addToDictionary(self):
        Word.__TranslitWords.append(self.__text)   
        
    # When "Dismiss" is clicked, word is added to "dictionary"/list 
    # of English words, will not be flagged as incorrect again, and will not
    # be suggested as an alternative word 
    def dismiss(self):
        # match format (lower case and no punctuation) to __EngWords
        lowerWord = self.__text.lower()
        lowerWord = stripPunct(lowerWord)
        
        Word.__EngWords.append(lowerWord)
        print(Word.__EngWords[-1])
    
    # "getters" for attributes
    def getText(self):      return self.__text
    def getIndex(self):     return self.__wordindex
    def flagged(self):      return self.__flag
    def getWidth(self):     return self.__w
    def getHeight(self):    return self.__h
    def getLocStats(self):  return self.__locationStats    
    def top3(self):         return self.__top3    

# end of Word class #
    
# functions as they are used chronologically:
# returns starting punctuation of a word
def startPunct(word):
    
    startPunct = ""
    
    while word[0] in ALL_PUNCT:
        startPunct += word[0]
        word = word[1:]
   
    return startPunct    
    
    
# returns ending punctuation of a word
def endPunct(word):
    
    endPunct = ""
    
    while word[-1] in ALL_PUNCT:
        endPunct = word[-1] + endPunct
        word = word[:-1]
   
    return endPunct      


# strip punctuation from word
def stripPunct(word):
    
    if len(word) > 1: # word must have at least 2 characters
    
        orginalWord = word
                
        while word[0] in ALL_PUNCT:
            word = word[1:]
        
        while word[-1] in ALL_PUNCT:
            word = word[:-1]
        
         # if after stripping there's no string, then the entire word is punct.
        if len(word) < 1:
            return originalWord #returning the original, i.e. just punctuation
    
    return word
    

# renders stylized logo in given place and size, returns coordinates of logo
# so words can be rendered relative to it
def dikdukio(size, x, y):
    Draw.setFontBold(True)
    Draw.setColor(Draw.BLACK)
    Draw.setFontSize(size)
    dikduk = Draw.string("dikduk", x, y)
    Draw.setColor(Draw.RED)
    dot = Draw.string(".", dikduk[2], y)
    Draw.setColor(Draw.BLACK)
    io = Draw.string("io", dot[2], y)
    Draw.setFontBold(False)

    return io


# draws white boxes with shadows underneath    
def shadowBox(startX, startY, endW, endH):
    # create shadow hues
    grays = [Draw.color(i, i, i) for i in range(240, 210, -1)]

    # draw shadow boxes, slightly offset from each other
    for i in range(len(grays)):
        Draw.setColor(grays[i])
        Draw.filledRect(startX - 10 + (i / 2), startY + 10 - i / 4, endW - i / 7, endH)

    # draw white box on top of the shadow
    Draw.setColor(Draw.WHITE)
    Draw.filledRect(startX, startY, endW, endH)


# rendering the start screen, calls UI function
def startScreen():
    Draw.setBackground(Draw.color(240, 240, 240))
    Draw.setFontFamily("Helvetica")

    # starting positions x,y, and w,h of the central prompt box
    promptX, promptY = CANVAS_WIDTH / 8, CANVAS_HEIGHT / 8
    promptW, promptH = CANVAS_WIDTH - CANVAS_WIDTH / 4, CANVAS_HEIGHT - CANVAS_HEIGHT / 4

    # Box that prompts user to enter the file name
    shadowBox(promptX, promptY, promptW, promptH)

    # Title and rendering
    Draw.setColor(Draw.BLACK)
    Draw.setFontSize(20)
    Draw.string("Welcome to", promptX + 360, promptY + 35)
    logo = dikdukio(30, promptX + 202, promptY + 70)
    Draw.setFontBold(True)
    title = Draw.string("Transliteration Editor", logo[2] + 7, promptY + 70)
    Draw.setFontBold(False)

    # introductory text
    Draw.setFontSize(20)
    Draw.wrappedString(intro, promptX + 40, title[3] + 30, promptW - 65)

    # File input space
    Draw.setFontSize(14)
    Draw.setFontItalic(True)
    Draw.setColor(Draw.GRAY)
    Draw.string("File Name:", promptX + 200, promptY + promptH - 125)
    Draw.setFontItalic(False)
    Draw.line(promptX + 200, promptY + promptH - 70, promptX + 590, promptY + promptH - 70)

    Draw.show()
    
    # returns the initial x, y, and w for reset white box on top of Enter File 
    # so the typed text can be covered if there is a mistake
    return promptX + 195, promptY + promptH - 95, promptX + 590 - 200

# user clicks and typing on the startScreen
def startScreenUI(restartX, restartY, restartW):      
    
    # emputy string to store fileName
    fileName = ""                   

    # first key to refernce position of rendered letters off of
    prevKey = [Draw.string(" ", CANVAS_WIDTH / 8 + 195, CANVAS_HEIGHT / 8 + 525)]
    
    # styling for the text in on enter text line
    Draw.setFontSize(20)
    Draw.setColor(Draw.BLACK)
    
    # user interaction (typing + clicking)
    while True:

        # stores value of key typed
        key = ""

        if Draw.hasNextKeyTyped():
            
            # store typed key
            key = Draw.nextKeyTyped()
            
            # store position so next key can be rendered based off it
            positionLastKey = prevKey[-1]
            
            # set max length of file so the text doesn't extend beyond the 
            # designated entry line and so the text can be covered by reset box
            fileNameMaxLength = 26
            fileOverMaxLength = len(fileName) > fileNameMaxLength

            # if the return key is pressed, then try to open file from fileName
            if key == "Return":

                fileName = str(fileName)
                
                try:
                    # test if file can be opened based on entered file name
                    file = open(fileName)
                    return fileName
                
                # if it doesn't open because it doesn't exist, clear Draw 
                # screen and area to render text, and and render error message
                except:
                    # with error message
                    fileName = key = ""
                    Draw.setColor(Draw.WHITE)
                    
                    # cover previously typed letters - incorrect file
                    Draw.filledRect(restartX, restartY, restartW, 25)
                    
                    # cover error message - too long
                    Draw.filledRect(CANVAS_WIDTH / 8 + 600, CANVAS_WIDTH / 8 + CANVAS_HEIGHT - CANVAS_HEIGHT / 4 - 150, 200, 40)
                    
                    # render "File not found in folder" message
                    Draw.setColor(Draw.RED)
                    Draw.setFontSize(14)
                    firstLine = Draw.string("Your file is was not found in this folder.\nEnter the name of a .txt file saved in this folder.", CANVAS_WIDTH / 8 + 200, CANVAS_HEIGHT - CANVAS_HEIGHT / 5)
                    
                    # reset styling for entered letters from typing
                    Draw.setColor(Draw.BLACK)
                    Draw.setFontSize(20)
                    prevKey = [Draw.string(" ", CANVAS_WIDTH / 8 + 195, CANVAS_HEIGHT / 8 + 525)]
                    positionLastKey = prevKey[-1]
            
            # delete previous letter from screen and fileName variable
            if key == "BackSpace":

                # draw a white box over previous letter
                if len(fileName) > 0:
                    Draw.setColor(Draw.WHITE)
                    Draw.filledRect(positionLastKey[0], positionLastKey[1], positionLastKey[2] - positionLastKey[0], positionLastKey[3] - positionLastKey[1])

                    # update truncate previous letters
                    fileName = fileName[:-1]
                    prevKey = prevKey[:-1]
                    Draw.setColor(Draw.BLACK)
                    
            # if the key is a letter or number and there is space left in filename
            elif key in validKeys_letNums and not fileOverMaxLength:

                # add key to fileName and Draw, add position to prevKey
                fileName += key
                prevKey.append(Draw.string(key, positionLastKey[2] - 1,
                                           positionLastKey[1]))

            # if the key special character (SHIFT, !, ", ?, etc.) and there 
            # is space left in filename
            elif key in validKeys_other:

                key = validKeys_other[key]
                fileName += key
                prevKey.append(Draw.string(key, positionLastKey[2] - 1,
                                           positionLastKey[1]))

            # if file reachs max length, display error message and reset value 
            # for word styling and so the display mesage doesn't last forever
            elif fileOverMaxLength:
                Draw.setColor(Draw.RED)
                Draw.setFontSize(13)
                Draw.string("File name is too long.\nShorten file name\nbefore proceeding.",
                            CANVAS_WIDTH / 8 + 600,
                            CANVAS_WIDTH / 8 + CANVAS_HEIGHT - CANVAS_HEIGHT / 4 - 150)
                Draw.setColor(Draw.BLACK)
                Draw.setFontSize(20)
                fileOverMaxLength = False


# based on valid user file name, import file as a list of words
def txtFileImport(fileName):      
    # creates list of words from the file to be edited
    file = open(fileName)
    uneditedWords = [ ]

    # inputs each paragraph
    for p in file:
        # splitting with " " (and not with the default option)
        # in order to keep the punctuation and find the \n for the enter
        paragraph = p.split(" ")

        # isolating the "\n" from the last word in the
        # paragraph to indicate paragraph breaks when rendering
        paragraph[-1] = paragraph[-1][:-1]

        # adding it back as its own string
        paragraph.append("\n")

        # add paragraph to list of words
        uneditedWords += paragraph

    file.close()
    return uneditedWords


# draws all circleButtons with text
def circleButton(x, y, w, text, fontSize, buttonColor, textColor=Draw.WHITE):
    Draw.setColor(buttonColor)
    Draw.filledOval(x, y, w, w)
    Draw.setFontSize(fontSize)
    Draw.setColor(textColor)
    Draw.string(text, x + w / 2.5, y + w / 4.5)

    # x1, x2, y1, y2
    return [x, x + w, y, y + w]

# determines whether to draw and drawss forward, back, save, and 
#pageNumber circleButtons
def drawButtons(curPage, uneditedWords, pageList, paperX):
    # initialize "blank" buttons to be passed through the function, will change
    # based on conditions below to or not to appear
    saveFile = back = forward =  [0,0,0,0]
    
    # current page number
    circleButton(740, 55, 40, curPage, 15, Draw.WHITE, Draw.BLACK)    

    # "<" back button
    if curPage > 1:
        back = circleButton(690, 55, 40, "<", 15, Draw.RED)
    
    # only render ">" forward button if there are pages left to render based on
    # "average words per page" 
    # if overall there are less than 175 words (hard-coded average for 1 page
    # documents) then there should not be a ">" button
    if curPage == 1 and len(uneditedWords) < 175:
        saveFile = circleButton(paperX, 20, 40, "✓", 15, Draw.RED)
    
    # otherwise if it's the first page, and there will be more pages, 
    # render it
    elif curPage == 1:
        forward = circleButton(790, 55, 40, ">", 15, Draw.RED)
    
    # ...but the question is, after the first page, until when is ">" rendered
    # so we aproximate num of total pages from average number of words per page
    else:
            
        avgWordsPerPage = pageList[-1] - pageList[-2] # "average" est.
        
        # if curPage is not the last page, show ">"
        if (pageList[-1] - 1) + avgWordsPerPage <= len(uneditedWords):  
            forward = circleButton(790, 55, 40, ">", 15, Draw.RED)
        
        # if curPage is the last page, render "Save" instead
        else: 
            saveFile = circleButton(paperX, 20, 40, "✓", 15, Draw.RED)
            
    return forward, back, saveFile


# renders word within the bounds of the paper and stores each position in
# list of renderd Words in the Word class
def renderWords(uneditedWords, paperX, paperY, paperW, paperH, pageList):
    
    # set default styling for words
    Draw.setColor(Draw.BLACK)
    wordSize = 26
    Draw.setFontSize(wordSize)

    # amount of pixels to offset the beginning of a line
    topMargin = 20

    # x - starting position of each line 
    startingX = paperX + topMargin

    # upper left corner coordinate of current word, 
    curX = startingX
    curY = paperY + topMargin

    # words cannot go to the right of the side margin
    sideMargin = paperX + paperW - 25

    # words cannot go underneath the bottom margin
    bottomMargin = 70

    # start from the first word on the page, based on what was stored on
    # the n - 1th page (initialized at 0 for the 0th page)
    indexCurWord = pageList[-1]

    # renders words - while there is still vertical space on page
    while curY + wordSize < CANVAS_HEIGHT - bottomMargin and indexCurWord < len(uneditedWords):

        # create and render word off screen to determine word width and height 
        # and see if/where it should fit horizontally on the page
        word = Word(uneditedWords[indexCurWord], indexCurWord)
        locWord = word.render(curX, -500, wordSize)
             
        # if the character is a \n, reset x position and increase y
        if word.getText() == "\n":
     
            curX = startingX
            curY += VERT_WORD_SPACE + wordSize + PARAGRAPH_SPACING

        # if the word can be rednered after the current x position and the width
        # won't exceed the side margin 
        elif locWord[1] < sideMargin:
            
            # draw again the right place, but use current y variable
            word.render(curX, curY, wordSize)

            # add to the list of rendered words
            word.toRenderList()
            
            # increment curX so it's in the correct position for the next word
            curX += word.getWidth() + HORIZ_WORD_SPACE 

        # no horizontal space, so reset x positon and increase y position
        else:
            
            curX = startingX
            curY += VERT_WORD_SPACE + wordSize
            
            # Check if there is still vertical space before attempting to render 
            # the next word, and if there is
            if curY + wordSize < CANVAS_HEIGHT - bottomMargin:
        
                # render word
                word.render(curX, curY, wordSize)
                word.toRenderList()
                
                
                curX += word.getWidth() + HORIZ_WORD_SPACE
                
            else: 
               # don't increment the curWord so it can be set as the last word 
               # of this page
                indexCurWord -= 1
                
        # increment so the next word can be rendered / set as the first word
        # on the next page
        indexCurWord += 1
    
    # add the first word of the next page to pagelist so on the next page, 
    # the rendering can pick up where it left off
    pageList.append(indexCurWord)

    # after all words place, show page
    Draw.show()
    return pageList

# renders the paper and buttons of the edit screen, calls UI function    
def editScreen(fileName, pageList, uneditedWords):

    # clear screen
    Draw.clear()
    
    # represents the number of the current page
    curPage = len(pageList)
    
    # render logo in upper-right corner
    dikdukio(25, CANVAS_WIDTH - 125, 15)
    
    # draw paper
    paperX, paperY, paperW, paperH = 30, 100, 800, 800
    shadowBox(paperX, paperY, paperW, paperH) 
    
    # draw buttons
    forward, back, saveFile = drawButtons(curPage, uneditedWords, pageList, paperX) 
    
    # renders number of words per page
    # Outputs pageList + "index" of the first word on next (unrendered) page to pageList
    pageList = renderWords(uneditedWords, paperX, paperY, paperW, paperH, pageList)
    Draw.show()
    
    # returns list of Word objects rendered on page
    clickableWords = Word.clickableWords(pageList)
    
    # user clicks for editScreen    
    while True:
        editScreenUI(pageList, forward, back, saveFile, uneditedWords, 
                     Word.clickableWords(pageList), fileName)
        

# clicks for rendered editScreen for circleButtons and words
def editScreenUI(pageList, forward, back, save, uneditedWords, 
                 clickableWords, fileName): 
    
    if Draw.mousePressed():
        
        clickX = Draw.mouseX()
        clickY = Draw.mouseY()
        
        # if forward button is clicked, "reset screen" and render next page
        if clickX > forward[0] and clickX < forward[1] and \
           clickY > forward[2] and clickY < forward[3]:
            
            # re-render page
            Draw.clear()
            pageList = editScreen(fileName, pageList, uneditedWords)
       
            
        # if back button is clicked, "reset screen" and render previous page
        if clickX > back[0] and clickX < back[1] and \
           clickY > back[2] and clickY < back[3]:

            Draw.clear()
            
            # delete previous page of words in clickableWords list
            Word.backPage(pageList)
            
            # remove last page from pageList so it renders the previous page, 
            # not the same one again
            pageList = pageList[:-2] 
            
            # re-render page
            Draw.clear()
            pageList = editScreen(fileName, pageList, uneditedWords)
        
        # save button, render endScreen
        if clickX > save[0] and clickX < save[1] and \
           clickY > save[2] and clickY < save[3]:
            
            # re-render page
            Draw.clear()
            endScreen(uneditedWords, fileName)        

        # loop to check if the flagged Words were clicked
        for word in clickableWords:
            if word.clicked(clickX, clickY):
                popupWindow(word, fileName, pageList, uneditedWords)
    

# draw popup window
def popupWindow(word, fileName, pageList, uneditedWords):
    
    # draw red box around word
    Draw.setColor(Draw.RED)
    coords = word.getLocStats()
    Draw.rect(coords[0]-1, coords[2]-1, coords[1] - coords[0] + 1, 
              coords[3] - coords[2])    
    
    # render popup window 
    Draw.setFontItalic(True)
    shadowBox(853, 230, 230, 315)
    
    #line from word to window
    Draw.setColor(Draw.RED)
    Draw.line(831, (coords[3] - (coords[3]-coords[2])/2), 852, 530/2)   
    
    # text on popup window
    Draw.rect(863, 240, 210, 50)
    inpopup = word.render(870, 250, 24)
    
    Draw.setColor(Draw.GRAY)
    Draw.setFontSize(13)
    Draw.string("Did you mean...", 865, 300)
    
    # add to dictionary and dismiss 
    Draw.setColor(Draw.RED)
    Draw.setFontSize(16)
    addToDictionary = Draw.string("Add to dictionary", 870, 480)            
    dismiss = Draw.string("Dismiss", 870, addToDictionary[3] + 10)        
    
    Draw.setFontItalic(False)
    
    # render suggested words
    replacements = word.top3()
    replX = 870
    replY = 330
    replWords = [ ]
    for w in replacements:
        replWords += [Word(w)]
        replWords[-1].render(replX, replY, 25)
        replY += 50
    
    popupWindowUI(word, fileName, pageList, uneditedWords, replWords,
                  addToDictionary, dismiss)
    
# popup window UI
def popupWindowUI(word, fileName, pageList, uneditedWords, replWords, 
                  addToDictionary, dismiss):

    # clickabibity of popUp 
    while True:
        
        if Draw.mousePressed():
            
            clickX = Draw.mouseX()
            clickY = Draw.mouseY()
             
            # check if each replacement word is clicked
            for repl in replWords:
                if repl.clicked(clickX, clickY):
                    
                    # replace current word with replacement word uneditedWords 
                    # so the corrected word can be rendered next time with
                    # punctuation from word since the replacements were
                    # generated from stripped words
                    uneditedWords[word.getIndex()] = (startPunct(word.getText())
                                                      + repl.getText() + 
                                                      endPunct(word.getText()))
                    # incrediment edit counter
                    Word.editMade()
                    
                    # render screen again to reflect edits
                    editScreen(fileName, pageList[:-1], uneditedWords)            
            
            # clicking "Add to dictionary" - don't change current word and 
            # add to translit words dictionary so it can be suggested in future
            # comparisions
            if clickX > addToDictionary[0] and clickX < addToDictionary[2] and \
               clickY > addToDictionary[1] and clickY < addToDictionary[3]:
                word.addToDictionary()
                editScreen(fileName, pageList[:-1], uneditedWords)
                
            # clicking "Dismiss" - don't change current word and 
            # add to english words dictionary so it will not be flagged again
            if clickX > dismiss[0] and clickX < dismiss[2] and \
               clickY > dismiss[1] and clickY < dismiss[3]:
                word.dismiss()
                editScreen(fileName, pageList[:-1], uneditedWords)            


# turns a list of words into a large string so output can be written to a .txt  
def outputEdits(wordslist):
    
    outputStr = ""
    for w in wordslist:
        outputStr += w + " "
    
    return outputStr

# writes output to new file, returns string of all words for docStats()
def writeOutput(editedWords, fileName):
    editedFile = "edited_" + fileName
    editedString = outputEdits(editedWords)
    revised = open(editedFile, "w")
    revised.write(editedString)
    revised.close()
    
    return editedString, editedFile

# calculates statitics about words, sentences, readability, etc based on
# the list of words and the string of words
def docStats(editedWords, editedString):
    
    # calculations for "Counts" section of document stats
    num_paragraphs = editedWords.count("\n")
    total_chars = len(editedString)
    num_words = editedString.count(" ") + 1
    num_sentences = editedString.count(". ") + editedString.count("! ") + \
                    editedString.count("? ")
    
    # dictionary of titles and calculations to render "Counts"
    counts = {" words": num_words, " characters":total_chars, 
              " sentences":num_sentences, " paragraphs":num_paragraphs}
    
    # calculations for "Averages" section of document stats    
    avg_sent_per_paragraph = round(num_sentences / num_paragraphs, 1)
    avg_word_per_sent = round(num_words / num_sentences, 1)
    
    # dictionary of titles and calculations to render "Averages"    
    averages = {" sentences per paragraph":avg_sent_per_paragraph, 
                " words per sentence":avg_word_per_sent}
    
    # calculations for "Estimated Readability" section of document stats, 
    # readibility is estimated because the Flesch calculations aren't as 
    # precise since the number of syllables is guesstimated
    
    # average syllable length is three letters (Courtesy of Nirmaldasan)
    avg_syllable_length = 3
    arpox_num_syllables = sum([round(len(word) / avg_syllable_length) for word 
                               in editedWords if len(word) > 1])
   
    # Readability Score Formulas (Courtesy of WebFX)
    # approximation of "a ranking scale of 0-100... Low scores indicate text 
    # that is complicated to understand" (WebFX).
    flecsh_reading_ease = (round(206.835 - (1.015 * avg_word_per_sent) - 
                                 (84.6 * (arpox_num_syllables/num_words)), 1))
    
    # approximates "the American school grade you would need to be in 
    # to comprehend the material on the page" (WebFX).
    flesch_kincaid_grade = (round((0.39 * avg_word_per_sent) + 
                                  (11.8 * (arpox_num_syllables/num_words)) - 
                                  15.59, 1))
    
    # dictionary of titles and calculations to render "Estimated Readability" 
    readability = {" Flesch Reading Ease Score":flecsh_reading_ease, 
                   " Flesch-Kincaid Grade Level":flesch_kincaid_grade}
    
    stats = {"Counts:":counts, "Averages:":averages, 
             "Estimated Readability:":readability}
    
    return stats

# executes functions that generate output file, statistics about doc, and 
# renders those results
def endScreen(editedWords, fileName):
    
    # write file output
    editedString, editedFile = writeOutput(editedWords, fileName)
    
    # generate doc stats
    stats = docStats(editedWords, editedString)
    
    # Draw new end screen
    Draw.setBackground(Draw.color(240, 240, 240))

    # starting positions x,y, and w,h of the central box with results
    promptX, promptY = CANVAS_WIDTH / 7 + 25, CANVAS_HEIGHT / 5 + 75
    promptW, promptH = CANVAS_WIDTH - CANVAS_WIDTH / 3, CANVAS_HEIGHT - CANVAS_HEIGHT / 3 - 150

    # Box that shows results
    shadowBox(promptX, promptY, promptW, promptH)  
    
    # logo in upperRight Corner
    dikdukio(25, CANVAS_WIDTH - 125, 15)
    
    # number of changes message in upper-left corner
    Draw.setColor(Draw.BLACK)
    
    # returns total amount of edits
    edits = Word.TotalEdits()
    
    # determine grammar in message based on amount of edits
    change_s = "changes"
    have_has = "have"
    
    if edits == 1: 
        change_s = change_s[:-1]
        have_has = "has"
    
    # render successful file save message
    Draw.setFontSize(20)
    s = "The " + str(edits) + " " + str(change_s) + " that you made " + have_has \
        + " been successfully saved.\n\nYou will find your edits in the file \"" \
        + editedFile + "\" in the same folder as \"" + fileName + ".\""
    Draw.wrappedString(s, promptX + 20, promptY + 65, promptW/2 - 20)

    
    # render thank you message
    Draw.setFontSize(24)
    Draw.string("Thank you for using", promptX + 90, promptY + 265)
    logo = dikdukio(34, promptX + 110, promptY + 295)
    Draw.setFontBold(True)
    Draw.setFontSize(34)
    Draw.string("!", logo[2], logo[1])

    # render document stats box and title
    Draw.setColor(Draw.RED)
    Draw.rect(promptX + promptW/2 + 40, promptY + 50, 300, 325)
    Draw.setFontSize(20)
    Draw.string("Your Document Stats:", promptX + promptW/2 + 85, promptY + 25)
    
    
    # loop to render the rest of the stat dictionaries based on starting position
    # and incrementing the y position
    titleX = promptX + promptW/2 + 50
    titleY = promptY + 60
    
    Draw.setFontSize(18)
    for s in stats:
        
        # render title per section
        Draw.setFontSize(18)
        Draw.setFontBold(True)
        countsTitle = Draw.string(s, titleX, titleY)
        
        # increment x and y positions to "indent" for sub-values
        countsX, countsY = countsTitle[0] + 20, countsTitle[3] + 5
        data = stats[s]
        
        for d in data:
            # render number bolded
            Draw.setFontBold(True)
            num = Draw.string(data[d], countsX, countsY)
            Draw.setFontBold(False)
            
            # render category italicized
            Draw.setFontSize(17)
            Draw.setFontItalic(True)
            category = Draw.string(d, num[2], countsY)
            countsY += 22
            Draw.setFontItalic(False)
        
        # paragraph break
        titleY = countsY + 18
    

def main():
    
    # import lists of transliterated and English words
    Word.importtranslit()
    Word.importenglish()

    # List of the # word printed on the page, initialized to word 0
    # Subsequent values are the number of word in list that is the first on each 
    # page: 0th word on 0th page, index last word of 0th page + 1 on 1st page, etc.
    pageList = [0]
    
    # create canvas
    Draw.setCanvasSize(CANVAS_WIDTH, CANVAS_HEIGHT)
    
    # render start screen
    restartX, restartY, restartW = startScreen()
    
    # run start screen UI until a valid file name is returned
    fileName = startScreenUI(restartX, restartY, restartW)
    
    # create a list of words from the text file to edit
    uneditedWords = txtFileImport(fileName)
    
    # render edit screen
    editScreen(fileName, pageList, uneditedWords)

main()