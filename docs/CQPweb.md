# XML/VRT
- XML-escape tokens and attributes
- for CQPweb, there has to be an XML-tag <text> with unique IDs
- only a relatively small number of <text>s are possible (up to ~ 100,000, preferably fewer)
- make sure all categorical meta data (including IDs) are valid MySQL-identifiers (whitelist = [A-Za-z_])
- you can only use categorical meta data on the <text> level for subcorpus creation and restricted queries
- keep it simple: no nesting of attributes

## file contents

    <corpus>

    <text id="" month="" ..>

    <tweet id="" author="" .. >
    <s>
    word \t pos \t lexeme ...
    word \t pos \t lexeme ...
    word \t pos \t lexeme ...
    </s>
    <s>
    word \t pos \t lexeme ...
    ...
    </s>
    </tweet>

    <tweet> id="" month="" ..>
    ...
    </tweet>

    ...

    </text>

    <text id="" month="" ..>
    ...
    </text>

    ...
    
    <text id="" month="" ..>
    ...
    </text>

    </corpus>
