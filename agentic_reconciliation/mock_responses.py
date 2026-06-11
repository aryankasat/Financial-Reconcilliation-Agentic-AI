MOCK_RESPONSES = {
    # 1. Unmatched Ledger: Amazon - Office Equipment (Outstanding transaction)
    "led_264a780d": {
        "categorise": {
            "category": "Timing Difference",
            "reasoning": "The transaction was recorded in the general ledger on 2026-06-29 for $124.80, but it does not appear on the June credit card statement. This is highly likely an outstanding transaction that cleared in the next billing cycle (July)."
        },
        "rca": {
            "analysis": (
                "RCA FINDINGS:\n"
                "1. Queried `ledger_entries` for the ID `led_264a780d`. The entry represents a charge of $124.80 at 'Amazon - Office Equipment' by Bob Brown with date 2026-06-29.\n"
                "2. Searched the `card_statement_lines` for transactions with amount 124.80. No matches were found on the June statement.\n"
                "3. By querying database entries after June 30 (or checking subsequent transaction data), we confirm this is an outstanding ledger item. It represents a typical timing difference where the transaction was initiated at the end of the month (June 29) but was not posted by the card provider until the next period (July 2)."
            ),
            "suggested_queries": [
                "SELECT * FROM ledger_entries WHERE id = 'led_264a780d';",
                "SELECT * FROM card_statement_lines WHERE amount = 124.80;"
            ]
        },
        "decide": {
            "decision_status": "AUTO_RESOLVED",
            "recommended_action": "Mark as outstanding timing difference. No action needed as this will reconcile naturally with the July statement.",
            "suggested_fix": "No adjustment required. Keep ledger entry in PENDING/OUTSTANDING state until July reconciliation is executed."
        }
    },
    
    # 2. Unmatched Card: Uber Trip Ride (Alice Johnson) - Missing Receipt
    "crd_cd1461ae": {
        "categorise": {
            "category": "Missing Ledger Entry",
            "reasoning": "The credit card statement shows a charge of $42.50 from UBER *TRIP RIDE on 2026-05-14 by Alice Johnson, but there is no corresponding ledger entry. This indicates the employee swiped the card but did not submit a receipt or log the expense."
        },
        "rca": {
            "analysis": (
                "RCA FINDINGS:\n"
                "1. Verified credit card statement charge `crd_cd1461ae` for UBER on 2026-05-14 for $42.50 cardholder Alice Johnson.\n"
                "2. Queried the general ledger for entries around 2026-05-14 with a similar amount. No entries were found near $42.50.\n"
                "3. Verified Alice Johnson's card last four digits ('3333'). Checked other ledger entries for Alice Johnson; she has other Uber entries but not for this date or amount. The card charge is authentic (matching standard Uber metadata) but lacks a corresponding accounting book record, meaning the receipt was not submitted."
            ),
            "suggested_queries": [
                "SELECT * FROM card_statement_lines WHERE id = 'crd_cd1461ae';",
                "SELECT * FROM ledger_entries WHERE amount BETWEEN 40.00 AND 45.00 AND transaction_date BETWEEN '2026-05-11' AND '2026-05-17';"
            ]
        },
        "decide": {
            "decision_status": "REQUIRES_HUMAN_INTERVENTION",
            "recommended_action": "Flag for employee review. Contact Alice Johnson to submit the missing receipt for the $42.50 Uber ride on 2026-05-14.",
            "suggested_fix": "Once the receipt is submitted, record a journal entry: Debit Travel Expenses $42.50, Credit acc_card_corp $42.50."
        }
    },

    # 3. Unmatched Card: The Steakhouse (Jane Doe) - Missing Receipt
    "crd_c74cfb78": {
        "categorise": {
            "category": "Missing Ledger Entry",
            "reasoning": "A charge of $185.50 at THE STEAKHOUSE CHICAGO on 2026-06-12 by Jane Doe appears on the card statement but is missing in the ledger, suggesting a missing receipt/expense submission."
        },
        "rca": {
            "analysis": (
                "RCA FINDINGS:\n"
                "1. Inspected card statement line `crd_c74cfb78`: $185.50 charge on 2026-06-12 at THE STEAKHOUSE CHICAGO for Jane Doe.\n"
                "2. Searched general ledger entries for amount $185.50 and nearby dates (2026-06-10 to 2026-06-15). No matches found.\n"
                "3. Checked Jane Doe's account details. The transaction is consistent with business dining but lacks ledger registration. It requires receipt verification and subsequent book entry."
            ),
            "suggested_queries": [
                "SELECT * FROM card_statement_lines WHERE id = 'crd_c74cfb78';",
                "SELECT * FROM ledger_entries WHERE amount BETWEEN 180.00 AND 190.00 AND transaction_date BETWEEN '2026-06-10' AND '2026-06-15';"
            ]
        },
        "decide": {
            "decision_status": "REQUIRES_HUMAN_INTERVENTION",
            "recommended_action": "Flag for CEO review. Contact Jane Doe's assistant to obtain the receipt and business purpose for the $185.50 Steakhouse charge.",
            "suggested_fix": "Create ledger entry: Debit Meals & Entertainment $185.50, Credit acc_card_corp $185.50."
        }
    },

    # 4. Unmatched Card: Electronics Direct (Bob Brown) - Potential Fraud
    "crd_18124945": {
        "categorise": {
            "category": "Unrecognized Card Charge (Potential Fraud)",
            "reasoning": "A large charge of $450.00 from ELECTRONICS DIRECT ONLINE on 2026-06-22 by Bob Brown does not have any corresponding ledger entry and matches high-risk characteristics (high amount, electronics merchant category MCC 5732)."
        },
        "rca": {
            "analysis": (
                "RCA FINDINGS:\n"
                "1. Analyzed card statement line `crd_18124945` - $450.00 on 2026-06-22 at ELECTRONICS DIRECT ONLINE, cardholder Bob Brown, MCC 5732 (Electronic Sales).\n"
                "2. Queried database for similar amounts in ledger. No matching entries or transactions exist. \n"
                "3. Consulted historical records for Bob Brown. There is no pre-authorization or office supply budget entry for this. The merchant name and high amount, combined with the lack of any purchase request, flag this as highly suspicious for potential fraud/unauthorized credit card use."
            ),
            "suggested_queries": [
                "SELECT * FROM card_statement_lines WHERE id = 'crd_18124945';",
                "SELECT * FROM ledger_entries WHERE amount = 450.00;"
            ]
        },
        "decide": {
            "decision_status": "REQUIRES_HUMAN_INTERVENTION",
            "recommended_action": "Urgent! Flag as potential fraud. Contact Bob Brown immediately to confirm if he authorized this $450.00 charge. If unauthorized, lock the card and file a charge dispute with the bank.",
            "suggested_fix": "Freeze Bob Brown's card ending in '4444' and initiate chargeback. Record a temporary fraud receivable entry if card provider does not reverse immediately."
        }
    },

    # 5. Discrepancy: Shopify CAD Storefront (Multi-Currency Mismatch)
    "led_9fcfc98d": {
        "categorise": {
            "category": "Amount Discrepancy",
            "reasoning": "The ledger amount is $200.00 (CAD) but the card statement shows $148.50 (USD), representing a variance of -$51.50. This is a multi-currency transaction discrepancy."
        },
        "rca": {
            "analysis": (
                "RCA FINDINGS:\n"
                "1. Inspected ledger entry `led_9fcfc98d`: recorded as $200.00 CAD on Shopify CAD Storefront. \n"
                "2. Inspected matching card statement line `crd_e5bdd36a`: billed as $148.50 USD, but lists a foreign currency of CAD and foreign amount of 202.00.\n"
                "3. Identified the root cause: there is a mismatch of 2.00 CAD between the ledger entry (200.00 CAD) and the card statement's foreign amount (202.00 CAD). The USD billing amount of $148.50 corresponds to 202.00 CAD at the conversion rate. The ledger entry was misrecorded at 200.00 CAD (likely ignoring a foreign transaction fee or exchange rate adjustment)."
            ),
            "suggested_queries": [
                "SELECT * FROM ledger_entries WHERE id = 'led_9fcfc98d';",
                "SELECT * FROM card_statement_lines WHERE id = 'crd_e5bdd36a';"
            ]
        },
        "decide": {
            "decision_status": "AUTO_RESOLVED",
            "recommended_action": "Reconcile the transactions by adjusting the ledger entry to match the actual card statement billing. Post a foreign exchange variance/adjustment of $1.47 USD (equivalent to the 2 CAD difference).",
            "suggested_fix": "Adjust ledger entry `led_9fcfc98d` amount from 200.00 CAD to 202.00 CAD, resulting in a USD cost of $148.50, and post the exchange variance adjustment."
        }
    },
    "crd_e5bdd36a": {
        "categorise": {
            "category": "Amount Discrepancy",
            "reasoning": "The card statement lists $148.50 USD for Shopify subscription but the ledger has $200.00 (recorded in CAD), creating a variance of -$51.50 due to multi-currency mismatch."
        },
        "rca": {
            "analysis": (
                "RCA FINDINGS:\n"
                "1. Inspected ledger entry `led_9fcfc98d`: recorded as $200.00 CAD on Shopify CAD Storefront. \n"
                "2. Inspected matching card statement line `crd_e5bdd36a`: billed as $148.50 USD, but lists a foreign currency of CAD and foreign amount of 202.00.\n"
                "3. Root cause: The ledger entry was recorded at exactly 200.00 CAD. The bank statement lists the transaction as 202.00 CAD, which was billed as $148.50 USD. The 2 CAD difference accounts for the variance."
            ),
            "suggested_queries": [
                "SELECT * FROM ledger_entries WHERE id = 'led_9fcfc98d';",
                "SELECT * FROM card_statement_lines WHERE id = 'crd_e5bdd36a';"
            ]
        },
        "decide": {
            "decision_status": "AUTO_RESOLVED",
            "recommended_action": "Reconcile the transactions by adjusting the ledger entry to match the actual card statement billing. Post a foreign exchange variance/adjustment.",
            "suggested_fix": "Update ledger `led_9fcfc98d` amount to match statement billing of $148.50 USD (202.00 CAD)."
        }
    },

    # 6. Discrepancy: Bob Brown Chipotle lunch (Tip variance)
    "led_bf5a09cf": {
        "categorise": {
            "category": "Amount Discrepancy",
            "reasoning": "The ledger recorded $15.00 but the card statement cleared at $18.50, causing a variance of $3.50. This is typical for restaurant purchases where the tip is omitted in the initial ledger entry."
        },
        "rca": {
            "analysis": (
                "RCA FINDINGS:\n"
                "1. Inspected ledger entry `led_bf5a09cf` recorded by Bob Brown for 'Chipotle lunch' on 2026-05-20 for $15.00.\n"
                "2. Inspected matching card statement line `crd_65a7e4d5` for CHIPOTLE 1234 on 2026-05-20 clearing at $18.50.\n"
                "3. The variance of exactly $3.50 is due to a tip/tax added at the point of sale but not recorded in the ledger by the employee. This is a standard meal tip discrepancy."
            ),
            "suggested_queries": [
                "SELECT * FROM ledger_entries WHERE id = 'led_bf5a09cf';",
                "SELECT * FROM card_statement_lines WHERE id = 'crd_65a7e4d5';"
            ]
        },
        "decide": {
            "decision_status": "AUTO_RESOLVED",
            "recommended_action": "Auto-resolve by adjusting the ledger entry amount to include the $3.50 tip.",
            "suggested_fix": "Increase ledger entry `led_bf5a09cf` from $15.00 to $18.50. Classify the $3.50 difference as meals expense (tip)."
        }
    },
    "crd_65a7e4d5": {
        "categorise": {
            "category": "Amount Discrepancy",
            "reasoning": "The card statement lists $18.50 for Chipotle, while the ledger has $15.00, creating a variance of $3.50, likely due to a restaurant tip."
        },
        "rca": {
            "analysis": (
                "RCA FINDINGS:\n"
                "1. Inspected ledger entry `led_bf5a09cf` recorded by Bob Brown for 'Chipotle lunch' on 2026-05-20 for $15.00.\n"
                "2. Inspected matching card statement line `crd_65a7e4d5` for CHIPOTLE 1234 on 2026-05-20 clearing at $18.50.\n"
                "3. Root cause: The employee recorded the pre-tip subtotal of $15.00 in the ledger. The card transaction cleared with a $3.50 tip, totaling $18.50."
            ),
            "suggested_queries": [
                "SELECT * FROM ledger_entries WHERE id = 'led_bf5a09cf';",
                "SELECT * FROM card_statement_lines WHERE id = 'crd_65a7e4d5';"
            ]
        },
        "decide": {
            "decision_status": "AUTO_RESOLVED",
            "recommended_action": "Adjust the ledger entry amount to include the $3.50 tip.",
            "suggested_fix": "Increase ledger entry `led_bf5a09cf` amount to $18.50."
        }
    },

    # 7. Discrepancy: JetBrains Subscription (FX Fluctuation / Conversion Fee)
    "led_75433628": {
        "categorise": {
            "category": "Amount Discrepancy",
            "reasoning": "The ledger has $100.00 for JetBrains Subscription but the card statement shows $102.45, resulting in a variance of $2.45. This matches patterns of currency conversion rates or foreign transaction fees."
        },
        "rca": {
            "analysis": (
                "RCA FINDINGS:\n"
                "1. Inspected ledger entry `led_75433628` for 'JetBrains Subscription' recorded as $100.00 on 2026-06-15.\n"
                "2. Inspected card statement line `crd_f60ac85d` for 'JETBRAINS S.R.O. PRAGUE' on 2026-06-15 clearing at $102.45.\n"
                "3. Verified that the merchant 'JETBRAINS S.R.O.' is located in Prague (Czech Republic) and transactions are processed internationally. The $2.45 variance is the exact foreign transaction fee (approx 2.5%) or minor exchange rate fluctuation applied by the card issuer, which was not factored into the ledger entry."
            ),
            "suggested_queries": [
                "SELECT * FROM ledger_entries WHERE id = 'led_75433628';",
                "SELECT * FROM card_statement_lines WHERE id = 'crd_f60ac85d';"
            ]
        },
        "decide": {
            "decision_status": "AUTO_RESOLVED",
            "recommended_action": "Auto-resolve by posting a minor exchange fee adjustment of $2.45 to reconcile the ledger with the bank statement.",
            "suggested_fix": "Increase ledger entry `led_75433628` from $100.00 to $102.45, debiting the $2.45 variance to Bank Fees / Exchange Rate Adjustment account."
        }
    },
    "crd_f60ac85d": {
        "categorise": {
            "category": "Amount Discrepancy",
            "reasoning": "The card statement shows $102.45 for JetBrains in Prague, while the ledger has $100.00. The $2.45 difference represents an foreign transaction fee or conversion variance."
        },
        "rca": {
            "analysis": (
                "RCA FINDINGS:\n"
                "1. Inspected ledger entry `led_75433628` for 'JetBrains Subscription' recorded as $100.00 on 2026-06-15.\n"
                "2. Inspected card statement line `crd_f60ac85d` for 'JETBRAINS S.R.O. PRAGUE' on 2026-06-15 clearing at $102.45.\n"
                "3. Root cause: The subscription is billed from Prague, Czech Republic. The card statement amount includes a 2.45% international transaction/conversion fee, bringing the total to $102.45, whereas the ledger only recorded the base subscription amount of $100.00."
            ),
            "suggested_queries": [
                "SELECT * FROM ledger_entries WHERE id = 'led_75433628';",
                "SELECT * FROM card_statement_lines WHERE id = 'crd_f60ac85d';"
            ]
        },
        "decide": {
            "decision_status": "AUTO_RESOLVED",
            "recommended_action": "Adjust ledger entry to account for international fee of $2.45.",
            "suggested_fix": "Increase ledger entry `led_75433628` to $102.45 to include the foreign transaction fee."
        }
    }
}
