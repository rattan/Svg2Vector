
import re

from VdPath import VdPath

# Parse a VectorDrawables XML file, and generate an internal tree representaion,
# which can be used for drawing / previewing.

class VdParser:
    @classmethod
    def nextStart(cls, s, end):
        while end < len(s):
            c = s[end]
            # Note that 'e' or 'E' are not valid path commands, but could be
            # used for floating point numbers' scientific notation.
            # Therefore, when searching for next command, we should ignore 'e'
            # and 'E'
            if ((ord(c) - ord('A')) * (ord(c) - ord('Z')) <= 0 or ((ord(c) - ord('a')) * (ord(c) - ord('z')) <= 0)) and c != 'e' and c != 'E':
                return end
            end += 1
        return end

    @classmethod
    def addNode(cls, nList, cmd, val):
        nList.append(VdPath.Node(cmd, val))

    @classmethod
    def parsePath(cls, value):
        start = 0
        end = 1
        nList = []
        while end < len(value):
            end = cls.nextStart(value, end)
            s = value[start: end]
            val = cls.getFloats(s)

            cls.addNode(nList, s[0], val)

            start = end
            end += 1
        
        if end - start == 1 and start < len(value):
            cls.addNode(nList, value[start], [])
        return nList

    class ExtractFloatResult:
        def __init__(self):
            # We need to return the position of the next separator and whether the
            # next float starts with a '-' or a '.'.
            self.mEndPosition = 0
            self.mEndWithNegOrDot = False
    

    # Copies elements from {@code original} into a new array, from indexes start (inclusive) to
    # end (exclusive). The original order of elements is preserved.
    # If {@code end} is greater than {@code original.length}, the result is padded
    # with the value {@code 0.0f}.
    # @param original the original array
    # @param start the start index, inclusive
    # @param end the end index, exclusive
    # @return the new array
    # @throws ArrayIndexOutOfBoundsException if {@code start < 0 || start > original.length}
    # @throws IllegalArgumentException if {@code start > end}
    # @throws NullPointerException if {@code original == null}
    @classmethod
    def copyOfRange(cls, original, start, end):
        if start > end:
            raise ValueError()
        originalLength = len(original)
        if start < 0 or start > originalLength:
            raise IndexError()
        resultLength = end - start
        copyLength = min(resultLength, originalLength - start)
        result = []
        for i in range(start, start + copyLength):
            result.append(original[i])
        return result

    # Calculate the position of the next comma or space or negative sign
    # @param s the string to search
    # @param start the position to start searching
    # @param result the result of the extraction, including the position of the
    # the starting position of next number, whether it is ending with a '-'.
    @classmethod
    def extract(cls, s, start, result):
        # Now lookgin for ' ', ',', '.' or '-' from the start.
        currentIndex = start
        foundSaperator = False
        result.mEndWithNegOrDot = False
        secondDot = False
        isExponential = False
        while currentIndex < len(s):
            isPrevExponential = isExponential
            isExponential = False
            currentChar = s[currentIndex]
            if currentChar in [' ', ',']:
                foundSaperator = True
            elif currentChar == '-':
                # The negative sign following a 'e' or 'E' is not a separator.
                if currentIndex != start and not isPrevExponential:
                    foundSaperator = True
                    result.mEndWithNegOrDot = True
            elif currentChar == '.':
                if not secondDot:
                    secondDot = True
                else:
                    # This is the second dot, and it is considered as a separator.
                    foundSaperator = True
                    result.mEndWithNegOrDot = True
            elif currentChar in ['e', 'E']:
                isExponential = True

            if foundSaperator:
                break
            currentIndex += 1
        # When there is nothing found, then we put the end position to the end
        # of the string.
        result.mEndPosition = currentIndex


    # Parse the floats in the string this is an optimized version of parseFloat(s.split(",/\\s"));
    # @param s the string containing a command and list of floats
    # @return arry of floats
    @classmethod
    def getFloats(cls, s):
        if s[0] == 'z' or s[0] == 'Z':
            return []
        results = [0.0] * len(s)
        count = 0
        startPosition = 1
        endPosition = 0

        result = cls.ExtractFloatResult()
        totalLength = len(s)

        # The startPosition should always be the first character of the
        # current number, and endPosition is the character after the current
        # number.
        while startPosition < totalLength:
            cls.extract(s, startPosition, result)
            endPosition = result.mEndPosition
            
            if startPosition < endPosition:
                results[count] = float(s[startPosition: endPosition])
                count += 1
            
            if result.mEndWithNegOrDot:
                # Keep the '-' or '.' sign with next number.
                startPosition = endPosition
            else:
                startPosition = endPosition + 1
        return cls.copyOfRange(results, 0, count)
    