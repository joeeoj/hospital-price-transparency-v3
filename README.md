# About the tables (must read)

### The `hospitals` table

Schema:

```sql
create table hospitals (
    cms_certification_num char(6),
    name varchar(256),
    address varchar(256),
    city varchar(128),
    state char(2),
    zip5 char(5),
    beds int,
    phone_number char(10),
    homepage_url varchar(2048),
    chargemaster_url varchar(2048),
    last_edited_by_username varchar(32),
    constraint user_submits_non_empty_row check (
    	(last_edited_by_username and chargemaster_url and homepage_url) or
    	(not last_edited_by_username and not chargemaster_url and not homepage_url)
    	),
    primary key (cms_certification_num)
);
```

This table is mostly filled out. However there are a few fields that aren't.

#### `homepage_url`

Hospital homepage.

#### `chargemaster_url`

This can be a direct link to the hospital chargemaster, or the URL of the page that contains or links to the chargemaster. All I care about is that it takes me less than 5 seconds to find it.

#### `last_edited_by_username` (!!)

In order to get credit for a hospital that you added prices to (or edited the prices of) **you have to put your name in the column `last_edited_by_username`** in the row **corresponding to that hospital.**

### `prices`

Schema:

```sql
create table prices (
    cms_certification_num char(6),
    payer varchar(256),
    code varchar(128) default 'NONE',
    internal_revenue_code varchar(128) default 'NONE',
    units varchar(128),
    description varchar(2048),
    inpatient_outpatient enum('INPATIENT', 'OUTPATIENT', 'BOTH', 'UNSPECIFIED') default 'UNSPECIFIED',
    price decimal(10,2) NOT NULL,
    code_disambiguator varchar(2048) default 'NONE',
    constraint price_less_than_zero check (price >= 0),
    constraint price_greater_than_ten_mil check (price <= 1E+7),
    constraint payer_not_empty check (trim(payer) != ""),
    constraint code_not_empty check (trim(code) != ""),
    constraint internal_revenue_code_not_empty check (trim(code) != ""),
    constraint desc_not_empty check (trim(description) != ""),
    constraint strings_trimmed check (
        payer = trim(payer) and
        code = trim(code) and
        internal_revenue_code = trim(internal_revenue_code) and
        description = trim(description)
        ),

    foreign key (cms_certification_num) references hospitals(cms_certification_num),
    primary key (cms_certification_num, code, inpatient_outpatient, internal_revenue_code, code_disambiguator, payer)
);
```

Some of the fields (`code`, `internal_revenue_code`) will be automatically populated with `NONE` if they're not entered.

#### `cms_certification_num`

(Foreign Key) ID of the hospital in question. Comes from the `hospitals` table.

#### `payer`

Either `CASH PRICE`, `GROSS CHARGE`, `MAX`, `MIN`, or `Insurance company ABC` or whoever the payer is. 

Strip off semantic information from the payer, e.g. 

`Insurance Co ABC__derived contracted rate` becomes `Insurance Co ABC`.
`ABC HMO CORP NEGOTIATED RATE` becomes `ABC HMO CORP`.
`Negotiated Charge: NMH CIGNA HMO AND OAP _336_` becomes `NMH CIGNA HMO AND OAP _336_`

Common synonyms:

**CASH PRICE**: use this instead of "Cash:", "Discounted Cash", "Discounted Cash Price", "Self", or "Self-pay", etc.
**GROSS CHARGE**: use this instead of "Gross", "List price", "Gross Charges", "Charge", etc.
**MAX**: use this instead of "Max de-identified rate", "Deidentified maximum", "De-identified Maximum Negotiated Charge", etc.
**MIN**: similar to above

#### `code`

If not given, put `'NONE'` or leave the whole column blank and it will be populated with `'NONE'` automatically.

The **code** column is the CPT/HCPCS/DRG code or some kind of hospital-agnostic code. Nulls will be converted to `NONE`. 

**DO NOT MAKE DUPLICATE CODES** like `C137,1`, `C137,2`. This is a disaster for the schema. Use the `code_disambiguator` column if you have to.

##### code modifiers:

Sometimes there's a column in the chargemaster called `modifier`. Append this to the end of the code with a hypen.

So `C1377` + `GN` as a modifier becomes `C1377-GN`.
#### `internal_revenue_code`

If not given, put `'NONE'` or leave the whole column blank and it will be populated with `'NONE'` automatically.

The internal code the hospital uses for charges. Useful for disambiguating two charges with the same code and description -- not useful really for anything else.

This is the same as "item number", for example.

Nulls will be converted to `NONE`.

#### `units`

Sometimes codes come with a unit string ("1 unit", "2 ccs", etc.)

#### `description`

String description of the service. If you need to concatenate two fields together to get a complete description you can.

#### `inpatient_outpatient`

If not given, put `'UNSPECIFIED'` or leave the whole column blank and it will be populated with `'UNSPECIFIED'` automatically.

Inpatient/outpatient must be either `INPATIENT`, `OUTPATIENT`, `BOTH`, or `UNSPECIFIED`. `UNSPECIFIED` is assumed to mean, "no information given." 

#### `price`

The price that goes with the payer. A payer is either `GROSS CHARGE`, `CASH PRICE`, `MIN`, `MAX`, or `Some Insurance Co. ABC HMO` (you get the idea).

#### `code_disambiguator`

If not given, put `'NONE'` or leave the whole column blank and it will be populated with `'NONE'` automatically.

This column is for anything needed to avoid creating duplicate codes like `C137,1`, `C137,2`. Instead, put a `1` in the `code_disambiguator` column, or something like that.

For example if a hospital has two identical codes with different descriptions:

(Simplified example)

```markdown
| code         | description       | code_disambiguator |
|--------------|-------------------|--------------------|
| C1378        | short needle      | NONE               |
| C1379        | long needle 7mm   | 1                  |
| C1379        | long needle 10mm  | 2                  |
| C1380        | syringe body 9.0  | 1                  |
| C1380        | syringe body 9.1  | 2                  |
```

If the chargemaster provides a column which automatically disambiguates the rows (like description) you can use that too. And if a hospital has exactly duplicate rows in the chargemaster, you can simply drop them. 

It's a "catch-all" column to prevent code duplication -- leave as `'NONE'` or the whole column empty if you don't need to use it.

Important: do NOT put a random integer or UUID in this field in order to get around the PK collisions. This negates the point of the PKs in the first place.