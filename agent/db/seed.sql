-- FinVox Seed Data
-- Realistic Saudi financial services data
SET search_path TO finvox;

-- Relationship Managers
INSERT INTO relationship_managers VALUES
('RM001','Tariq Al-Dosari','+966501110001','tariq@finvox.sa','wealth',12,4500000,true,NOW()),
('RM002','Noura Al-Qahtani','+966501110002','noura@finvox.sa','loans',8,2800000,true,NOW()),
('RM003','Fahad Al-Shammari','+966501110003','fahad@finvox.sa','wealth',15,7200000,true,NOW()),
('RM004','Maha Al-Otaibi','+966501110004','maha@finvox.sa','loans',10,3100000,true,NOW());

-- Customers (10 realistic profiles)
INSERT INTO customers VALUES
('C001','Faisal Al-Dosari','+966551234567','faisal@gmail.com','1085432100','1985-03-15','Villa 12, Al-Malqa District','Riyadh','Saudi Arabia','valid','2027-01-15','aggressive','premium','RM001','en',true,NULL,'2022-06-01',NOW()),
('C002','Ahmed Al-Harbi','+966559876543','ahmed.h@gmail.com','1092345678','1990-07-22','Apt 5, King Fahd Road','Jeddah','Saudi Arabia','valid','2026-11-20','moderate','retail','RM002','ar',true,NULL,'2023-01-15',NOW()),
('C003','Sara Al-Ghamdi','+966541112233','sara.g@outlook.com','1078901234','1988-11-03','Tower B, Al-Olaya','Riyadh','Saudi Arabia','valid','2027-03-10','conservative','hnw','RM001','en',true,NULL,'2021-03-20',NOW()),
('C004','Mohammed Al-Zahrani','+966531234000','maz@yahoo.com','1065432198','1975-05-18','House 8, Al-Rawdah','Dammam','Saudi Arabia','expired','2026-02-28','moderate','premium','RM003','ar',false,NULL,'2020-08-10',NOW()),
('C005','Layla Al-Otaibi','+966571239876','layla.o@gmail.com','1087654321','1992-09-30','Apt 14, Tahlia Street','Jeddah','Saudi Arabia','valid','2027-06-15','aggressive','retail','RM002','en',true,NULL,'2024-02-01',NOW()),
('C006','Khalid Al-Rashidi','+966509998877','khalid.r@outlook.com','1054321098','1980-01-25','Villa 3, Al-Nakheel','Riyadh','Saudi Arabia','valid','2026-12-01','moderate','hnw','RM003','ar',true,NULL,'2019-11-15',NOW()),
('C007','Nora Al-Subaie','+966541234599','nora.s@gmail.com','1098765432','1995-12-10','Apt 22, Corniche Road','Khobar','Saudi Arabia','valid','2027-09-20','conservative','retail','RM004','en',false,NULL,'2024-06-15',NOW()),
('C008','Omar Al-Mutairi','+966551239988','omar.m@proton.me','1076543210','1982-04-08','House 15, Al-Sulay','Riyadh','Saudi Arabia','valid','2026-08-30','very_aggressive','premium','RM001','en',true,NULL,'2021-01-05',NOW()),
('C009','Hanan Al-Qahtani','+966539871234','hanan.q@gmail.com','1089012345','1993-06-14','Tower C, Al-Hamra','Jeddah','Saudi Arabia','pending','2026-03-01','moderate','retail','RM004','ar',false,NULL,'2025-01-10',NOW()),
('C010','Sultan Al-Dawsari','+966501234888','sultan.d@gmail.com','1067890123','1978-08-22','Villa 7, Al-Yasmin','Riyadh','Saudi Arabia','valid','2027-05-01','aggressive','uhnw','RM003','en',true,NULL,'2018-04-20',NOW());

-- Bank Accounts
INSERT INTO bank_accounts VALUES
('BA001','C001','Al Rajhi Bank','SA2880000001234567890','SA2880000001234567890123',true,NOW()),
('BA002','C001','Saudi National Bank','SA4410000009876543210','SA4410000009876543210123',false,NOW()),
('BA003','C002','Al Rajhi Bank','SA2880000002345678901','SA2880000002345678901234',true,NOW()),
('BA004','C003','HSBC Saudi','SA5540000003456789012','SA5540000003456789012345',true,NOW()),
('BA005','C004','Riyad Bank','SA2080000004567890123','SA2080000004567890123456',true,NOW()),
('BA006','C005','Al Rajhi Bank','SA2880000005678901234','SA2880000005678901234567',true,NOW()),
('BA007','C006','Saudi National Bank','SA4410000006789012345','SA4410000006789012345678',true,NOW()),
('BA008','C008','Gulf International Bank','SA6680000007890123456','SA6680000007890123456789',true,NOW()),
('BA009','C010','HSBC Saudi','SA5540000008901234567','SA5540000008901234567890',true,NOW()),
('BA010','C010','JP Morgan Saudi','SA7780000009012345678','SA7780000009012345678901',false,NOW());

-- Loans (realistic Saudi lending)
INSERT INTO loans VALUES
('L001','C001','home',1200000,890000,4.75,240,8500,'2023-01-01','2043-01-01','active','Villa 12 Al-Malqa','Primary residence',NOW()),
('L002','C001','personal',50000,32000,7.50,36,1580,'2024-06-15','2027-06-15','active',NULL,'Home renovation',NOW()),
('L003','C002','auto',120000,78000,5.25,60,2270,'2023-09-01','2028-09-01','active','2024 Toyota Camry','Vehicle purchase',NOW()),
('L004','C003','home',2500000,2100000,4.25,300,13200,'2022-03-01','2047-03-01','active','Tower B Al-Olaya','Investment property',NOW()),
('L005','C004','business',500000,420000,6.50,60,9800,'2024-01-15','2029-01-15','active','Business assets','Working capital',NOW()),
('L006','C004','personal',80000,65000,8.00,24,3620,'2025-06-01','2027-06-01','active',NULL,'Medical expenses',NOW()),
('L007','C005','auto',95000,88000,5.50,48,2210,'2025-01-01','2029-01-01','active','2025 Hyundai Tucson','Vehicle purchase',NOW()),
('L008','C006','home',3500000,2800000,4.00,360,16720,'2020-06-01','2050-06-01','active','Villa 3 Al-Nakheel','Primary residence',NOW()),
('L009','C008','personal',200000,145000,7.00,48,4790,'2024-03-01','2028-03-01','active',NULL,'Investment capital',NOW()),
('L010','C010','business',2000000,1650000,5.75,120,21800,'2022-01-01','2032-01-01','active','Company shares','Business expansion',NOW());

-- Loan Payments (recent months for active loans)
INSERT INTO loan_payments VALUES
('LP001','L001','2026-01-01',8500,8500,'2025-12-29','paid',0,'auto_debit','REF-L001-202601',NOW()),
('LP002','L001','2026-02-01',8500,8500,'2026-01-30','paid',0,'auto_debit','REF-L001-202602',NOW()),
('LP003','L001','2026-03-01',8500,8500,'2026-02-28','paid',0,'auto_debit','REF-L001-202603',NOW()),
('LP004','L001','2026-04-01',8500,0,NULL,'due',0,NULL,NULL,NOW()),
('LP005','L002','2026-01-15',1580,1580,'2026-01-14','paid',0,'bank_transfer','REF-L002-202601',NOW()),
('LP006','L002','2026-02-15',1580,1580,'2026-02-15','paid',0,'bank_transfer','REF-L002-202602',NOW()),
('LP007','L002','2026-03-15',1580,0,NULL,'due',0,NULL,NULL,NOW()),
('LP008','L003','2026-01-01',2270,2270,'2026-01-02','paid',0,'auto_debit','REF-L003-202601',NOW()),
('LP009','L003','2026-02-01',2270,2270,'2026-02-01','paid',0,'auto_debit','REF-L003-202602',NOW()),
('LP010','L003','2026-03-01',2270,0,NULL,'overdue',150,NULL,NULL,NOW()),
('LP011','L005','2026-01-15',9800,9800,'2026-01-15','paid',0,'auto_debit','REF-L005-202601',NOW()),
('LP012','L005','2026-02-15',9800,5000,'2026-02-20','partial',350,'bank_transfer','REF-L005-202602',NOW()),
('LP013','L005','2026-03-15',9800,0,NULL,'overdue',350,NULL,NULL,NOW()),
('LP014','L006','2025-12-01',3620,0,NULL,'overdue',500,NULL,NULL,NOW()),
('LP015','L006','2026-01-01',3620,0,NULL,'overdue',500,NULL,NULL,NOW()),
('LP016','L006','2026-02-01',3620,0,NULL,'overdue',500,NULL,NULL,NOW()),
('LP017','L008','2026-03-01',16720,16720,'2026-02-28','paid',0,'auto_debit','REF-L008-202603',NOW()),
('LP018','L009','2026-03-01',4790,4790,'2026-03-01','paid',0,'auto_debit','REF-L009-202603',NOW());

-- Loan Applications
INSERT INTO loan_applications VALUES
('LA001','C002','home',800000,240,'First home purchase','under_review','RM002','Income docs received, property valuation pending',NOW(),NOW()),
('LA002','C005','personal',30000,24,'Travel','pending','RM002',NULL,NOW(),NOW()),
('LA003','C007','auto',110000,48,'Vehicle purchase','docs_required','RM004','Awaiting salary certificate',NOW(),NOW()),
('LA004','C009','personal',45000,36,'Education','approved','RM004','Approved, awaiting disbursement',NOW(),NOW());

-- Funds (investment products - Saudi market)
INSERT INTO funds VALUES
('F001','Al Rajhi Saudi Equity Fund','equity','SAR',45.80,45.20,2800000000,4,2.1,5.8,18.5,42.0,68.0,1.25,5000,'https://finvox.sa/funds/F001.pdf',true,'2026-03-10',NOW()),
('F002','SAB Saudi Bond Fund','debt','SAR',12.35,12.30,1500000000,2,-0.2,0.8,4.2,12.5,22.0,0.85,1000,'https://finvox.sa/funds/F002.pdf',true,'2026-03-10',NOW()),
('F003','HSBC Saudi Balanced Fund','hybrid','SAR',28.90,28.50,950000000,3,1.5,3.2,12.8,28.0,45.0,1.10,3000,'https://finvox.sa/funds/F003.pdf',true,'2026-03-10',NOW()),
('F004','Riyad Money Market Fund','money_market','SAR',10.05,10.04,3200000000,1,0.4,1.2,5.1,15.2,25.0,0.45,1000,NULL,true,'2026-03-10',NOW()),
('F005','Al Rajhi Real Estate Fund','real_estate','SAR',22.15,21.80,680000000,3,1.8,4.5,15.2,35.0,52.0,1.50,10000,'https://finvox.sa/funds/F005.pdf',true,'2026-03-10',NOW()),
('F006','NCB Gold ETF','commodity','SAR',85.60,83.20,420000000,4,2.8,8.5,22.5,48.0,75.0,0.65,1000,NULL,true,'2026-03-10',NOW()),
('F007','SABB Sukuk Fund','sukuk','SAR',15.20,15.15,890000000,2,0.3,1.0,3.8,11.0,18.5,0.70,2000,'https://finvox.sa/funds/F007.pdf',true,'2026-03-10',NOW()),
('F008','Jadwa Saudi Equity Index Fund','equity','SAR',38.45,37.90,1200000000,4,1.4,4.2,16.2,38.0,62.0,0.35,5000,NULL,true,'2026-03-10',NOW()),
('F009','Al Rajhi Dividend Growth Fund','equity','SAR',52.30,51.80,750000000,3,1.0,3.5,14.8,32.0,55.0,1.15,5000,NULL,true,'2026-03-10',NOW()),
('F010','Gulf International Emerging Markets','equity','SAR',18.75,18.20,320000000,5,3.0,7.2,24.5,52.0,NULL,1.80,10000,'https://finvox.sa/funds/F010.pdf',true,'2026-03-10',NOW());

-- Portfolios
INSERT INTO portfolios VALUES
('P001','C001','Growth Portfolio','growth',350000,425000,21.4,7,'TASI',NOW()),
('P002','C001','Retirement Fund','balanced',200000,218000,9.0,5,'Balanced Index',NOW()),
('P003','C003','Wealth Preservation','conservative',1500000,1620000,8.0,3,'Bond Index',NOW()),
('P004','C003','Growth Allocation','growth',800000,960000,20.0,7,'TASI',NOW()),
('P005','C005','Starter Portfolio','balanced',25000,27500,10.0,5,'Balanced Index',NOW()),
('P006','C006','Core Holdings','balanced',2000000,2340000,17.0,6,'TASI',NOW()),
('P007','C008','Aggressive Growth','growth',500000,645000,29.0,9,'TASI',NOW()),
('P008','C008','Sharia Compliant','sharia_compliant',300000,336000,12.0,5,'Sharia Index',NOW()),
('P009','C010','Ultra Growth','growth',3000000,3750000,25.0,8,'TASI',NOW()),
('P010','C010','Income Portfolio','conservative',2000000,2140000,7.0,3,'Sukuk Index',NOW());

-- Holdings (portfolio fund allocations)
INSERT INTO holdings VALUES
('H001','P001','F001',3500,35.00,45.80,160300,37.7,37800,NOW()),
('H002','P001','F008',2800,32.00,38.45,107660,25.3,18060,NOW()),
('H003','P001','F006',700,68.00,85.60,59920,14.1,12320,NOW()),
('H004','P001','F005',2200,18.00,22.15,48730,11.5,9130,NOW()),
('H005','P001','F010',2600,14.50,18.75,48750,11.5,11050,NOW()),
('H006','P002','F003',3800,24.00,28.90,109820,50.4,18620,NOW()),
('H007','P002','F007',4000,13.50,15.20,60800,27.9,6800,NOW()),
('H008','P002','F004',4700,9.80,10.05,47235,21.7,1175,NOW()),
('H009','P003','F002',45000,11.00,12.35,555750,34.3,60750,NOW()),
('H010','P003','F007',40000,14.00,15.20,608000,37.5,48000,NOW()),
('H011','P003','F004',45000,9.50,10.05,452250,27.9,24750,NOW()),
('H012','P004','F001',8000,33.00,45.80,366400,38.2,102400,NOW()),
('H013','P004','F008',7500,30.00,38.45,288375,30.0,63375,NOW()),
('H014','P004','F010',8000,15.00,18.75,150000,15.6,30000,NOW()),
('H015','P004','F005',7000,19.50,22.15,155050,16.2,18550,NOW()),
('H016','P006','F001',15000,36.00,45.80,687000,29.4,147000,NOW()),
('H017','P006','F003',18000,25.00,28.90,520200,22.2,70200,NOW()),
('H018','P006','F005',20000,20.00,22.15,443000,18.9,43000,NOW()),
('H019','P006','F006',8000,72.00,85.60,684800,29.3,108800,NOW()),
('H020','P007','F001',5500,34.00,45.80,251900,39.1,64900,NOW()),
('H021','P007','F010',10000,16.00,18.75,187500,29.1,27500,NOW()),
('H022','P007','F008',5300,31.00,38.45,203785,31.6,39435,NOW()),
('H023','P009','F001',25000,35.00,45.80,1145000,30.5,270000,NOW()),
('H024','P009','F010',35000,15.50,18.75,656250,17.5,113750,NOW()),
('H025','P009','F008',20000,32.00,38.45,769000,20.5,129000,NOW()),
('H026','P009','F006',12000,70.00,85.60,1027200,27.4,187200,NOW()),
('H027','P010','F002',60000,11.50,12.35,741000,34.6,51000,NOW()),
('H028','P010','F007',50000,14.20,15.20,760000,35.5,50000,NOW()),
('H029','P010','F004',64000,9.70,10.05,643200,30.0,22400,NOW());

-- SIPs
INSERT INTO sips VALUES
('SIP001','P001','F001',5000,'monthly',15,'active','2024-01-15','2026-04-15',130000,26,NOW()),
('SIP002','P002','F003',3000,'monthly',1,'active','2024-06-01','2026-04-01',63000,21,NOW()),
('SIP003','P005','F003',2000,'monthly',10,'active','2024-03-10','2026-04-10',48000,24,NOW()),
('SIP004','P006','F001',10000,'monthly',5,'active','2023-01-05','2026-04-05',380000,38,NOW()),
('SIP005','P007','F010',8000,'monthly',20,'active','2024-01-20','2026-04-20',192000,24,NOW()),
('SIP006','P009','F008',15000,'monthly',1,'active','2023-06-01','2026-04-01',495000,33,NOW()),
('SIP007','P001','F006',3000,'quarterly',15,'active','2024-06-15','2026-06-15',24000,8,NOW());

-- Dividends
INSERT INTO dividends VALUES
('D001','P001','F009',2500,47.80,'2025-12-15','2025-12-20',true,NOW()),
('D002','P003','F002',8500,688.26,'2025-12-31','2026-01-05',false,NOW()),
('D003','P006','F001',12000,261.95,'2025-12-15','2025-12-20',true,NOW()),
('D004','P009','F001',25000,545.85,'2025-12-15','2025-12-20',true,NOW()),
('D005','P010','F007',6800,447.37,'2025-12-31','2026-01-05',false,NOW()),
('D006','P004','F001',6000,130.98,'2025-12-15','2025-12-20',true,NOW());

-- Recent Transactions
INSERT INTO transactions VALUES
('T001','P001','F001','sip',109.17,45.80,5000,0,'completed','SIP-202603-001','2026-03-15'),
('T002','P001','F006','buy',35.05,85.60,3000,15,'completed','TXN-202603-001','2026-03-05'),
('T003','P002','F003','sip',103.81,28.90,3000,0,'completed','SIP-202603-002','2026-03-01'),
('T004','P004','F001','buy',218.34,45.80,10000,25,'completed','TXN-202602-001','2026-02-20'),
('T005','P006','F001','sip',218.34,45.80,10000,0,'completed','SIP-202603-003','2026-03-05'),
('T006','P007','F010','buy',533.33,18.75,10000,25,'completed','TXN-202603-002','2026-03-08'),
('T007','P003','F002','sell',2000,12.35,24700,50,'completed','TXN-202603-003','2026-03-02'),
('T008','P009','F008','sip',390.12,38.45,15000,0,'completed','SIP-202603-004','2026-03-01'),
('T009','P005','F003','sip',69.20,28.90,2000,0,'completed','SIP-202603-005','2026-03-10'),
('T010','P001','F010','switch_out',500,18.75,9375,20,'completed','SW-202602-001','2026-02-15'),
('T011','P001','F008','switch_in',243.82,38.45,9375,0,'completed','SW-202602-002','2026-02-15');

-- Tickets
INSERT INTO tickets VALUES
('TK001','C002','loan','EMI payment issue','Auto-debit failed for March EMI, bank returned insufficient funds','high','open','RM002',NULL,NOW(),NULL),
('TK002','C004','kyc','KYC renewal required','KYC expired, customer notified via WhatsApp','medium','in_progress','RM004',NULL,NOW(),NULL),
('TK003','C001','investment','Fund switch query','Customer wants to switch from emerging markets to local equity','low','resolved','RM001','Switch executed on Feb 15, confirmation sent','2026-02-15','2026-02-16'),
('TK004','C006','account','Address update','Customer moved to new villa, needs address update across all accounts','medium','open','RM003',NULL,NOW(),NULL),
('TK005','C004','loan','Late fee dispute','Customer disputes late fees on personal loan L006, claims payment was made','high','escalated','RM004',NULL,NOW(),NULL);

-- Compliance Flags
INSERT INTO compliance_flags VALUES
('CF001','C004','kyc_expiry','KYC expired on 2026-02-28, customer not responsive to renewal requests','high','open',NOW(),NULL),
('CF002','C004','overdue_payment','3 consecutive missed payments on personal loan L006, total overdue SAR 10,860','critical','investigating',NOW(),NULL),
('CF003','C002','overdue_payment','March auto EMI returned, insufficient funds in primary account','medium','open',NOW(),NULL),
('CF004','C009','kyc_expiry','KYC pending since onboarding, documents not yet submitted','medium','open',NOW(),NULL),
('CF005','C010','risk_change','Recent aggressive trading pattern detected, risk profile review needed','low','open',NOW(),NULL);

-- Sample Interactions
INSERT INTO interactions VALUES
('INT001','C001','voice','inbound',245,'Customer asked about home loan balance and next EMI. Also inquired about portfolio performance.','Routine account inquiry, customer satisfied with portfolio returns.',
'positive','["get_loans","get_portfolio_summary"]','["identify_caller","get_loans","get_portfolio_summary","get_holdings"]',true,'sess_001','2026-03-01'),
('INT002','C004','voice','inbound',180,'Customer called about late fees on personal loan. Became frustrated when told fees cannot be waived without manager approval.','Dispute about late fees, escalated to RM.',
'negative','["get_loan_detail","explain_charges","create_ticket"]','["identify_caller","get_loans","get_payment_history","create_ticket"]',true,'sess_002','2026-03-05'),
('INT003','C003','whatsapp','inbound',NULL,'Customer requested portfolio statement for visa application via WhatsApp.','Statement generated and sent.',
'neutral','["generate_statement","send_statement"]','["identify_caller","get_portfolio_summary","send_statement"]',true,'sess_003','2026-03-08');

-- Documents
INSERT INTO documents VALUES
('DOC001','C001','national_id','National ID - Faisal',NULL,true,NOW()),
('DOC002','C001','income_proof','Salary Certificate 2025',NULL,true,NOW()),
('DOC003','C003','national_id','National ID - Sara',NULL,true,NOW()),
('DOC004','C003','bank_statement','HSBC Statement Q4 2025',NULL,true,NOW()),
('DOC005','C004','national_id','National ID - Mohammed',NULL,true,'2024-06-01'),
('DOC006','C004','income_proof','Tax Return 2024',NULL,false,NOW());
