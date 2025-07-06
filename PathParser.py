from enum import Enum

from VdPath import VdPath

# Utility functions for parsing path information. The implementation details should be the same as
# the PathParser in Android framework.
# <p>See https://www.w3.org/TR/SVG/paths.html#PathDataBNF for the pathData syntax.

class PathParser:
    EMPTY_FLOAT_ARRAY = []
    
    class ExtractFloatResult:
        def __init__(self):
            # The end position of the parameter.
            self.mEndPosition = 0
            # Whether there is an explicit separator after the end position or not.
            self.mExplicitSeparator = False

    # Determines the end position of a command parameter.
    # @param s the string to search
    # @param start the position to start searching
    # @param flagMode indicates Boolean flag syntax; a Boolean flag is either "0" or "1" and
    #     doesn't have to be followed by a separator
    # @param result the result of the extraction
    @classmethod
    def extract(cls, s: str, start: int, flagMode: bool, result: ExtractFloatResult):
        foundSeparator = False
        result.mExplicitSeparator = False
        secondDot = False
        isExponential = False
        # Looking for ' ', ',', '.' or '-' from the start.
        currentIndex = start
        while currentIndex < len(s):
            isPrevExponential = isExponential
            isExponential = False
            currentChar = s[currentIndex]
            if currentChar in [' ', ',']:
                foundSeparator = True
                result.mExplicitSeparator = True
            elif currentChar == '-':
                # The negative sign following a 'e' or 'E' is not an implicit separator.
                if currentIndex != start and not isPrevExponential:
                    foundSeparator = True
            elif currentChar == '.':
                if secondDot:
                    # Second dot is an implicit separator.
                    foundSeparator = True
                else:
                    secondDot = True
            elif currentChar in ['e', 'E']:
                isExponential = True
            
            if foundSeparator or flagMode and currentIndex > start:
                break
            currentIndex += 1
        # When there is nothing found, then we put the end position to the end of the string.
        result.mEndPosition = currentIndex

    class ParseMode(Enum):
        SVG = 1
        ANDROID = 2

    # Parses the floats in the string this is an optimized version of parseFloat(s.split(",|\\s"));
    # @param s the string containing a command and list of floats
    # @param parseMode indicated whether the path belongs to an either SVG or a vector drawable
    # @return array of floats
    @classmethod
    def getFloats(cls, s: str, parseMode: ParseMode):
        command = s[0]
        if command == 'z' or command == 'Z':
            return cls.EMPTY_FLOAT_ARRAY
        try:
            arcCommand = command == 'a' or command == 'A'
            results = [0.0] * len(s)
            count = 0
            startPosition = 1
            endPosition = 0
            result = cls.ExtractFloatResult()
            totalLength = len(s)
            # The startPosition should always be the first character of the current number, and
            # endPosition is the character after the current number.
            while startPosition < totalLength:
                # In ANDROID parse mode we treat flags as regular floats for compatibility with
                # old vector drawables that may have pathData not conforming to
                # https://www.w3.org/TR/SVG/paths.html#PathDataBNF. In such a case flags may be
                # represented by "1.0" or "0.0" (b/146520216).
                flagMode = parseMode == cls.ParseMode.SVG and arcCommand and (count % 7 == 3 or count % 7 == 4)
                cls.extract(s, startPosition, flagMode, result)
                endPosition = result.mEndPosition
                if startPosition < endPosition:
                    results[count] = float(s[startPosition: endPosition])
                    count += 1
                if result.mExplicitSeparator:
                    startPosition = endPosition + 1
                else:
                    startPosition = endPosition
            if arcCommand:
                # https://www.w3.org/TR/SVG/paths.html#ArcOutOfRangeParameters:
                # If either rx or ry have negative signs, these are dropped;
                # the absolute value is used instead.
                for i in range(0, count - 1, 7):
                    results[i] = abs(results[i])
                    results[i + 1] = abs(results[i + 1])
            return results[:count]
        except Exception as e:
            raise Exception(f'Error in parsing "{s}" {e}')

    @classmethod
    def addNode(cls, lst: list, cmd, val: list):
        lst.append(VdPath.Node(cmd, val))

    @classmethod
    def nextStart(cls, s: str, end: int):
        while end < len(s):
            c = s[end]
            # Note that 'e' or 'E' are not valid path commands, but could be used for floating
            # point numbers' scientific notation. Therefore, when searching for next command, we
            # should ignore 'e' and 'E'.
            if (ord('A') <= ord(c) and ord(c) <= ord('Z') and ord(c) != ord('E') or ord('a') <= ord(c) and ord(c) <= ord('z') and ord(c) != ord('e')):
                return end
            end += 1
        return end

    @classmethod
    def parsePath(cls, value: str, mode: ParseMode):
        value = value.strip()
        nList = []
        start = 0
        end = 1
        while end < len(value):
            end = cls.nextStart(value, end)
            s = value[start: end]
            currentCommand = s[0]
            val = cls.getFloats(s, mode)
            if start == 0:
                # For the starting command, special handling: add M 0 0 if there is none.
                # This is good for transformation.
                if currentCommand != 'M' and currentCommand != 'm':
                    cls.addNode(nList, 'M',  [0.0] * 2)
            cls.addNode(nList, currentCommand, val)
            start = end
            end += 1
        if end - start == 1 and start < len(value):
            cls.addNode(nList, value[start], cls.EMPTY_FLOAT_ARRAY)
        return nList

