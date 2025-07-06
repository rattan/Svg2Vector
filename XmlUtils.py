import math

class XmlUtils:
    # Formats the number and removes trailing zeros after the decimal dot and also the dot itself
    # if there were non-zero digits after it.
    #
    # @param value the value to be formatted
    # @return the corresponding XML string for the value
    @classmethod
    def formatFloatValue(cls, value: float):
        if not math.isfinite(value):
            raise ValueError(f'Invalid number: {value}')
        # Use locale-independent conversion to make sure that the decimal separator is always dot.
        # We use Float.toString as opposed to Double.toString to avoid writing too many
        # insignificant digits.
        result = str(value)
        return cls.trimInsignificantZeros(result)

    # Removes trailing zeros after the decimal dot and also the dot itself if there are no non-zero
    # digits after it. Use {@link #trimInsignificantZeros(String, DecimalFormatSymbols)} instead of
    # this method if locale specific behavior is desired.
    # 
    # @param floatingPointNumber the string representing a floating point number
    # @return the original number with trailing zeros removed
    # @classmethod
    # def trimInsignificantZeros(cls, floatingPointNumber = '.'):
    #     return trimInsignificantZeros(floatingPointNumber, '.', 'E')
    
    @classmethod
    def trimInsignificantZeros(cls, floatingPointNumber: str, decimalSeparator: str = '.', exponentialSeparator: str = 'E'):
        pos = floatingPointNumber.rfind(decimalSeparator)
        if pos < 0:
            return floatingPointNumber
        if pos == 0:
            pos = 2
        
        exponent = floatingPointNumber.upper().find(exponentialSeparator, pos)
        i = exponent if 0 <= exponent else len(floatingPointNumber) - 1
        while i > pos:
            if floatingPointNumber[i] != '0':
                i += 1
                break
            i -= 1
        if exponent < 0:
            return floatingPointNumber[:i]
        elif exponent == i:
            return floatingPointNumber
        else:
            return floatingPointNumber[:i] + floatingPointNumber[exponent]