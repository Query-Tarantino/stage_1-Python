# The whitespace that Java's String.strip removes (SPEC §1). Python's bare str.strip()
# also removes U+0085, U+00A0, U+2007 and U+202F, so every strip passes these
# characters instead: s.strip(JAVA_WHITESPACE).
JAVA_WHITESPACE = (
    "\t\n\x0b\x0c\r\x1c\x1d\x1e\x1f \u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006"
    "\u2008\u2009\u200a\u2028\u2029\u205f\u3000"
)
