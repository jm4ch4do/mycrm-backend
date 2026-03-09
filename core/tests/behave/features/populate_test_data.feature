Feature: Populate Test Data
    As a developer
    I want to populate the database with test data
    So that I can have a consistent test environment

    Scenario: Populate database with accounts
        Given I create "accounts" through the API
            | name                | status   | type     | owner_username | industry       | website                     |
            | Acme Corp           | active   | customer | testuser1      | Manufacturing  | https://acme.com            |
            | Tech Solutions      | active   | partner  | testuser1      | Software       | https://techsolutions.io    |
            | Global Trade        | active   | vendor   | testuser2      | Logistics      | https://globaltrade.com     |
            | Pinnacle Consulting | prospect | customer | testuser1      | Consulting     | https://pinnacle.co         |
            | Bright Horizons     | active   | customer | testuser2      | Education      | https://brighthorizons.edu  |
            | Nova Financial      | active   | partner  | testuser1      | Finance        | https://novafinancial.com   |
            | Summit Healthcare   | prospect | customer | testuser2      | Healthcare     | https://summithealth.org    |
            | Redwood Media       | active   | customer | testuser1      | Media          | https://redwoodmedia.com    |
            | Atlas Engineering   | inactive | vendor   | testuser2      | Engineering    | https://atlaseng.com        |
            | Cascade Systems     | active   | customer | testuser1      | Software       | https://cascadesys.io       |
            | Frontier Energy     | prospect | customer | testuser2      | Energy         | https://frontierenergy.com  |
            | Pacific Retail      | active   | customer | testuser1      | Retail         | https://pacificretail.com   |
            | Quantum Analytics   | active   | partner  | testuser1      | Technology     | https://quantumanalytics.ai |
            | Meridian Insurance  | active   | customer | testuser2      | Insurance      | https://meridianins.com     |
            | Blue Ocean Shipping | active   | vendor   | testuser1      | Transportation | https://blueoceanship.com   |
            | Apex Legal          | prospect | partner  | testuser2      | Legal          | https://apexlegal.com       |
            | Greenfield Farms    | active   | customer | testuser1      | Agriculture    | https://greenfieldfarms.com |
            | Stellar Aerospace   | active   | customer | testuser2      | Aerospace      | https://stellaraero.com     |
            | Iron Bridge Capital | prospect | partner  | testuser1      | Finance        | https://ironbridgecap.com   |
            | Velocity Motors     | active   | customer | testuser2      | Automotive     | https://velocitymotors.com  |
            | Sapphire Hotels     | inactive | customer | testuser1      | Hospitality    | https://sapphirehotels.com  |
            | Crestline Pharma    | active   | customer | testuser2      | Pharmaceutical | https://crestlinepharma.com |

    Scenario: Populate database with contacts
        Given I create "accounts" through the API
            | name                | status | type     |
            | Acme Corp           | active | customer |
            | Tech Solutions      | active | partner  |
            | Global Trade        | active | vendor   |
            | Pinnacle Consulting | active | customer |
            | Bright Horizons     | active | customer |
            | Nova Financial      | active | partner  |
            | Quantum Analytics   | active | partner  |
            | Meridian Insurance  | active | customer |
            | Stellar Aerospace   | active | customer |
            | Crestline Pharma    | active | customer |
        And I create "contacts" through the API
            | first_name | last_name | email                         | account_id          | role           | seniority | job_title                | department   | phone        | mobile       |
            | John       | Doe       | john.doe@acme.com             | Acme Corp           | decision_maker | executive | CEO                      | Executive    | 555-100-0001 | 555-200-0001 |
            | Sarah      | Chen      | sarah.chen@acme.com           | Acme Corp           | influencer     | senior    | VP of Engineering        | Engineering  | 555-100-0002 | 555-200-0002 |
            | Mike       | Johnson   | mike.j@acme.com               | Acme Corp           | user           | junior    | Software Developer       | Engineering  | 555-100-0003 |              |
            | Emily      | Williams  | emily.w@acme.com              | Acme Corp           | influencer     | senior    | Director of Operations   | Operations   | 555-100-0004 | 555-200-0004 |
            | Peter      | Zhang     | peter.z@acme.com              | Acme Corp           | influencer     | senior    | Head of Procurement      | Procurement  | 555-100-0005 | 555-200-0005 |
            | David      | Kim       | david.kim@techsol.com         | Tech Solutions      | decision_maker | executive | Managing Director        | Executive    | 555-101-0001 | 555-201-0001 |
            | Laura      | Martinez  | laura.m@techsol.com           | Tech Solutions      | influencer     | senior    | Head of Partnerships     | Sales        | 555-101-0002 | 555-201-0002 |
            | James      | Brown     | james.b@techsol.com           | Tech Solutions      | user           | junior    | Account Manager          | Sales        | 555-101-0003 |              |
            | Priya      | Patel     | priya.p@techsol.com           | Tech Solutions      | influencer     | senior    | Solutions Architect      | Engineering  | 555-101-0004 | 555-201-0004 |
            | Rachel     | Green     | rachel.g@globaltrade.com      | Global Trade        | decision_maker | senior    | Procurement Manager      | Procurement  | 555-102-0001 | 555-202-0001 |
            | Tom        | Wilson    | tom.w@globaltrade.com         | Global Trade        | user           | junior    | Logistics Coordinator    | Logistics    | 555-102-0002 |              |
            | Sophie     | Reynolds  | sophie.r@globaltrade.com      | Global Trade        | influencer     | senior    | Supply Chain Director    | Operations   | 555-102-0003 | 555-202-0003 |
            | Anna       | Taylor    | anna.t@pinnacle.com           | Pinnacle Consulting | decision_maker | executive | Partner                  | Executive    | 555-103-0001 | 555-203-0001 |
            | Mark       | Anderson  | mark.a@pinnacle.com           | Pinnacle Consulting | influencer     | senior    | Senior Consultant        | Consulting   | 555-103-0002 |              |
            | Olivia     | Clark     | olivia.c@pinnacle.com         | Pinnacle Consulting | user           | junior    | Business Analyst         | Consulting   | 555-103-0003 |              |
            | Lisa       | Thomas    | lisa.t@brighthorizons.com     | Bright Horizons     | decision_maker | senior    | Dean of Programs         | Education    | 555-104-0001 | 555-204-0001 |
            | Kevin      | Jackson   | kevin.j@brighthorizons.com    | Bright Horizons     | user           | junior    | Program Coordinator      | Education    | 555-104-0002 |              |
            | Maria      | Garcia    | maria.g@novafinancial.com     | Nova Financial      | decision_maker | executive | CFO                      | Finance      | 555-105-0001 | 555-205-0001 |
            | Robert     | Lee       | robert.l@novafinancial.com    | Nova Financial      | influencer     | senior    | Investment Director      | Investments  | 555-105-0002 | 555-205-0002 |
            | Aisha      | Khan      | aisha.k@novafinancial.com     | Nova Financial      | user           | junior    | Financial Analyst        | Finance      | 555-105-0003 |              |
            | Daniel     | Nguyen    | daniel.n@quantumai.com        | Quantum Analytics   | decision_maker | executive | CTO                      | Technology   | 555-106-0001 | 555-206-0001 |
            | Yuki       | Tanaka    | yuki.t@quantumai.com          | Quantum Analytics   | influencer     | senior    | Data Science Lead        | Research     | 555-106-0002 | 555-206-0002 |
            | Chris      | Morgan    | chris.m@quantumai.com         | Quantum Analytics   | user           | junior    | ML Engineer              | Engineering  | 555-106-0003 |              |
            | Patricia   | O'Brien   | patricia.o@meridianins.com    | Meridian Insurance  | decision_maker | executive | Chief Underwriting Off.  | Underwriting | 555-107-0001 | 555-207-0001 |
            | Samuel     | Rivera    | samuel.r@meridianins.com      | Meridian Insurance  | influencer     | senior    | Claims Director          | Claims       | 555-107-0002 | 555-207-0002 |
            | Helen      | Cooper    | helen.c@stellaraero.com       | Stellar Aerospace   | decision_maker | executive | VP of Defense Programs   | Programs     | 555-108-0001 | 555-208-0001 |
            | Nathan     | Brooks    | nathan.b@stellaraero.com      | Stellar Aerospace   | influencer     | senior    | Chief Engineer           | Engineering  | 555-108-0002 | 555-208-0002 |
            | Grace      | Liu       | grace.l@stellaraero.com       | Stellar Aerospace   | influencer     | senior    | Program Manager          | Programs     | 555-108-0003 | 555-208-0003 |
            | Victor     | Schmidt   | victor.s@crestlinepharma.com  | Crestline Pharma    | decision_maker | executive | Head of R&D              | Research     | 555-109-0001 | 555-209-0001 |
            | Rebecca    | Foster    | rebecca.f@crestlinepharma.com | Crestline Pharma    | influencer     | senior    | Clinical Trials Director | Clinical     | 555-109-0002 | 555-209-0002 |

    Scenario: Populate database with deals
        Given I create "accounts" through the API
            | name                | status | type     |
            | Acme Corp           | active | customer |
            | Tech Solutions      | active | partner  |
            | Pinnacle Consulting | active | customer |
            | Bright Horizons     | active | customer |
            | Nova Financial      | active | partner  |
            | Pacific Retail      | active | customer |
            | Quantum Analytics   | active | partner  |
            | Meridian Insurance  | active | customer |
            | Stellar Aerospace   | active | customer |
            | Crestline Pharma    | active | customer |
            | Global Trade        | active | vendor   |
        And I create "deals" through the API
            | name                        | account_id          | stage       | status | amount    | currency | probability | lead_source |
            | Acme Enterprise License     | Acme Corp           | proposal    | open   | 120000.00 | usd      | 60          | inbound     |
            | Acme Support Contract       | Acme Corp           | negotiation | open   | 45000.00  | usd      | 75          | referral    |
            | Acme Cloud Migration        | Acme Corp           | lead        | open   | 80000.00  | usd      | 20          | inbound     |
            | Acme Data Warehouse         | Acme Corp           | won         | won    | 300000.00 | usd      | 100         | outbound    |
            | Acme IoT Sensors            | Acme Corp           | lead        | open   | 65000.00  | usd      | 30          | outbound    |
            | Tech Solutions Partnership  | Tech Solutions      | won         | won    | 250000.00 | usd      | 100         | referral    |
            | Tech API Integration        | Tech Solutions      | proposal    | open   | 35000.00  | eur      | 50          | outbound    |
            | Tech Security Audit         | Tech Solutions      | lost        | lost   | 40000.00  | usd      | 0           | inbound     |
            | Tech DevOps Migration       | Tech Solutions      | lead        | open   | 72000.00  | usd      | 35          | inbound     |
            | Pinnacle Strategy Retainer  | Pinnacle Consulting | lead        | open   | 60000.00  | usd      | 15          | outbound    |
            | Pinnacle Digital Transform  | Pinnacle Consulting | proposal    | open   | 175000.00 | usd      | 40          | inbound     |
            | Pinnacle Change Management  | Pinnacle Consulting | negotiation | open   | 90000.00  | usd      | 65          | referral    |
            | Horizons LMS Platform       | Bright Horizons     | negotiation | open   | 95000.00  | usd      | 80          | inbound     |
            | Horizons Training Package   | Bright Horizons     | won         | won    | 30000.00  | eur      | 100         | outbound    |
            | Horizons Campus Expansion   | Bright Horizons     | lead        | open   | 200000.00 | usd      | 10          | inbound     |
            | Nova Portfolio Analytics    | Nova Financial      | proposal    | open   | 200000.00 | usd      | 55          | referral    |
            | Nova Compliance Suite       | Nova Financial      | lead        | open   | 150000.00 | usd      | 10          | inbound     |
            | Nova Risk Platform          | Nova Financial      | negotiation | open   | 320000.00 | usd      | 70          | inbound     |
            | Pacific POS Rollout         | Pacific Retail      | negotiation | open   | 110000.00 | usd      | 70          | outbound    |
            | Pacific Loyalty Program     | Pacific Retail      | lead        | open   | 50000.00  | usd      | 25          | inbound     |
            | Pacific E-commerce Platform | Pacific Retail      | proposal    | open   | 185000.00 | usd      | 45          | outbound    |
            | Quantum ML Pipeline         | Quantum Analytics   | proposal    | open   | 275000.00 | usd      | 50          | inbound     |
            | Quantum Data Lake           | Quantum Analytics   | lead        | open   | 140000.00 | usd      | 20          | inbound     |
            | Quantum Predictive Engine   | Quantum Analytics   | won         | won    | 190000.00 | usd      | 100         | referral    |
            | Meridian Claims Automation  | Meridian Insurance  | proposal    | open   | 230000.00 | usd      | 55          | outbound    |
            | Meridian Policy Platform    | Meridian Insurance  | lead        | open   | 160000.00 | usd      | 15          | inbound     |
            | Stellar Avionics Upgrade    | Stellar Aerospace   | negotiation | open   | 450000.00 | usd      | 75          | outbound    |
            | Stellar Telemetry System    | Stellar Aerospace   | proposal    | open   | 280000.00 | usd      | 40          | referral    |
            | Stellar Ground Control SW   | Stellar Aerospace   | lead        | open   | 120000.00 | usd      | 25          | inbound     |
            | Crestline Drug Discovery AI | Crestline Pharma    | lead        | open   | 500000.00 | usd      | 15          | outbound    |
            | Crestline Trial Management  | Crestline Pharma    | proposal    | open   | 180000.00 | eur      | 45          | referral    |
            | Global Trade Logistics SaaS | Global Trade        | negotiation | open   | 88000.00  | usd      | 60          | inbound     |
            | Global Trade Customs Portal | Global Trade        | lead        | open   | 55000.00  | eur      | 20          | outbound    |

    Scenario: Populate database with deal-contact associations
        Given I create "accounts" through the API
            | name                | status | type     |
            | Acme Corp           | active | customer |
            | Tech Solutions      | active | partner  |
            | Pinnacle Consulting | active | customer |
            | Nova Financial      | active | partner  |
            | Stellar Aerospace   | active | customer |
            | Quantum Analytics   | active | partner  |
        And I create "contacts" through the API
            | first_name | last_name | email                      | account_id          | role           | seniority |
            | John       | Doe       | john.doe@acme.com          | Acme Corp           | decision_maker | executive |
            | Sarah      | Chen      | sarah.chen@acme.com        | Acme Corp           | influencer     | senior    |
            | Emily      | Williams  | emily.w@acme.com           | Acme Corp           | influencer     | senior    |
            | Peter      | Zhang     | peter.z@acme.com           | Acme Corp           | influencer     | senior    |
            | David      | Kim       | david.kim@techsol.com      | Tech Solutions      | decision_maker | executive |
            | Laura      | Martinez  | laura.m@techsol.com        | Tech Solutions      | influencer     | senior    |
            | Priya      | Patel     | priya.p@techsol.com        | Tech Solutions      | influencer     | senior    |
            | Anna       | Taylor    | anna.t@pinnacle.com        | Pinnacle Consulting | decision_maker | executive |
            | Mark       | Anderson  | mark.a@pinnacle.com        | Pinnacle Consulting | influencer     | senior    |
            | Maria      | Garcia    | maria.g@novafinancial.com  | Nova Financial      | decision_maker | executive |
            | Robert     | Lee       | robert.l@novafinancial.com | Nova Financial      | influencer     | senior    |
            | Helen      | Cooper    | helen.c@stellaraero.com    | Stellar Aerospace   | decision_maker | executive |
            | Nathan     | Brooks    | nathan.b@stellaraero.com   | Stellar Aerospace   | influencer     | senior    |
            | Grace      | Liu       | grace.l@stellaraero.com    | Stellar Aerospace   | influencer     | senior    |
            | Daniel     | Nguyen    | daniel.n@quantumai.com     | Quantum Analytics   | decision_maker | executive |
            | Yuki       | Tanaka    | yuki.t@quantumai.com       | Quantum Analytics   | influencer     | senior    |
        And I create "deals" through the API
            | name                       | account_id          | stage       | status | amount    | currency |
            | Acme Enterprise License    | Acme Corp           | proposal    | open   | 120000.00 | usd      |
            | Acme Support Contract      | Acme Corp           | negotiation | open   | 45000.00  | usd      |
            | Acme Cloud Migration       | Acme Corp           | lead        | open   | 80000.00  | usd      |
            | Tech Solutions Partnership | Tech Solutions      | won         | won    | 250000.00 | usd      |
            | Tech API Integration       | Tech Solutions      | proposal    | open   | 35000.00  | eur      |
            | Pinnacle Strategy Retainer | Pinnacle Consulting | lead        | open   | 60000.00  | usd      |
            | Pinnacle Digital Transform | Pinnacle Consulting | proposal    | open   | 175000.00 | usd      |
            | Nova Portfolio Analytics   | Nova Financial      | proposal    | open   | 200000.00 | usd      |
            | Nova Risk Platform         | Nova Financial      | negotiation | open   | 320000.00 | usd      |
            | Stellar Avionics Upgrade   | Stellar Aerospace   | negotiation | open   | 450000.00 | usd      |
            | Stellar Telemetry System   | Stellar Aerospace   | proposal    | open   | 280000.00 | usd      |
            | Quantum ML Pipeline        | Quantum Analytics   | proposal    | open   | 275000.00 | usd      |
        And I add contact "john.doe@acme.com" to "deal" with "name" "Acme Enterprise License"
        And I add contact "sarah.chen@acme.com" to "deal" with "name" "Acme Enterprise License"
        And I add contact "peter.z@acme.com" to "deal" with "name" "Acme Enterprise License"
        And I add contact "emily.w@acme.com" to "deal" with "name" "Acme Support Contract"
        And I add contact "john.doe@acme.com" to "deal" with "name" "Acme Support Contract"
        And I add contact "sarah.chen@acme.com" to "deal" with "name" "Acme Cloud Migration"
        And I add contact "david.kim@techsol.com" to "deal" with "name" "Tech Solutions Partnership"
        And I add contact "laura.m@techsol.com" to "deal" with "name" "Tech Solutions Partnership"
        And I add contact "priya.p@techsol.com" to "deal" with "name" "Tech Solutions Partnership"
        And I add contact "david.kim@techsol.com" to "deal" with "name" "Tech API Integration"
        And I add contact "laura.m@techsol.com" to "deal" with "name" "Tech API Integration"
        And I add contact "anna.t@pinnacle.com" to "deal" with "name" "Pinnacle Strategy Retainer"
        And I add contact "mark.a@pinnacle.com" to "deal" with "name" "Pinnacle Strategy Retainer"
        And I add contact "anna.t@pinnacle.com" to "deal" with "name" "Pinnacle Digital Transform"
        And I add contact "maria.g@novafinancial.com" to "deal" with "name" "Nova Portfolio Analytics"
        And I add contact "robert.l@novafinancial.com" to "deal" with "name" "Nova Portfolio Analytics"
        And I add contact "maria.g@novafinancial.com" to "deal" with "name" "Nova Risk Platform"
        And I add contact "helen.c@stellaraero.com" to "deal" with "name" "Stellar Avionics Upgrade"
        And I add contact "nathan.b@stellaraero.com" to "deal" with "name" "Stellar Avionics Upgrade"
        And I add contact "grace.l@stellaraero.com" to "deal" with "name" "Stellar Avionics Upgrade"
        And I add contact "helen.c@stellaraero.com" to "deal" with "name" "Stellar Telemetry System"
        And I add contact "nathan.b@stellaraero.com" to "deal" with "name" "Stellar Telemetry System"
        And I add contact "daniel.n@quantumai.com" to "deal" with "name" "Quantum ML Pipeline"
        And I add contact "yuki.t@quantumai.com" to "deal" with "name" "Quantum ML Pipeline"

    Scenario: Populate database with bulk generated data
        Given I create "accounts" through the API
            | name         | status |
            | Bulk Corp    | active |
            | Bulk Partner | active |
            | Bulk Vendor  | active |
        And I generate "30" "contacts" with "account_id" "Bulk Corp" through the API
        And I generate "20" "contacts" with "account_id" "Bulk Partner" through the API
        And I generate "40" "deals" with "account_id" "Bulk Corp" through the API
        And I generate "25" "deals" with "account_id" "Bulk Partner" through the API
        And I generate "15" "deals" with "account_id" "Bulk Vendor" through the API
