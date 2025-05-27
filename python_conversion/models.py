from sqlalchemy import text

def get_dashboard_index_stats(db):
    sql = text("""
        SELECT state_abbr, county_name, 
            (sales_2009 / (1.0 * mailed_count) * 100) AS sales_rate,
            sales_2009, mailed_count
        FROM counties
        WHERE mailed_count IS NOT NULL
            AND mailed_count > sales_2009
            AND mailed_count > 10000
        ORDER BY (sales_2009 / (1.0 * mailed_count) * 100) DESC
        LIMIT 8
    """)
    result = db.session.execute(sql)
    top10 = []
    for row in result:
        row_dict = {key: value for key, value in row._mapping.items()}
        top10.append(row_dict)
    return top10

def get_dashboard_newdemos_states(db):
    ohio_sql = text("SELECT * FROM county_prospects WHERE state_code='OH' ORDER BY county_name")
    texas_sql = text("SELECT * FROM county_prospects WHERE state_code='TX' ORDER BY county_name")
    ohio_result = db.session.execute(ohio_sql)
    texas_result = db.session.execute(texas_sql)
    states = {
        'OH': [dict(row) for row in ohio_result],
        'TX': [dict(row) for row in texas_result]
    }
    return states

def get_dashboard_responder_file_data(db):
    sql = text("""
        SELECT coalesce(state_name, state, '') as state, 
            coalesce(total_dups,0) + coalesce(policy,0) AS total, 
            coalesce(policy,0) as policy_holders, 
            coalesce(total_dups,0) - coalesce(total,0) AS household_duplicates,
            coalesce(total,0) AS net
        FROM (
            SELECT coalesce(state,'') AS state, count(*) as policy
            FROM responder_file
            WHERE cust_flag = 'Y'
            GROUP BY coalesce(state, '')
            ) AS p
        FULL OUTER JOIN (
            SELECT state, count(*) AS total, sum(cnt) AS total_dups
            FROM (
                SELECT address_2, postal, coalesce(state, '') AS state, count(*) as cnt
                FROM responder_file
                WHERE coalesce(cust_flag, 'N') <> 'Y'
                GROUP BY address_2, postal, coalesce(state, '')
            ) AS hh
            GROUP BY state
        ) AS h1 USING (state)
        JOIN state_lookup ON (state = state_code)
    """)
    result = db.session.execute(sql)
    data = [dict(row) for row in result]
    fields = {
        'state': 'C',
        'total': 'N',
        'policy_holders': 'N',
        'household_duplicates': 'N',
        'net': 'N'
    }
    return {'data': data, 'fields': fields}
