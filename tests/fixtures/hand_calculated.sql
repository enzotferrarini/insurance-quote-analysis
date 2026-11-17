-- Five prospects, four quoted; eight quotes. Current snapshot 2026-02-28.
INSERT INTO prospects (id,first_name,last_name,created_at) VALUES
(1,'Demo','One','2026-01-01'),(2,'Demo','Two','2026-01-01'),
(3,'Demo','Three','2026-01-01'),(4,'Demo','Four','2026-01-01'),
(5,'Demo','Unquoted','2026-01-01');
INSERT INTO carriers VALUES (1,'Fictional Alder'),(2,'Fictional Birch');
INSERT INTO coverages VALUES (1,'Liability','Fixture'),(2,'Collision','Fixture');
INSERT INTO quotes VALUES
(1,1,1,'Auto',100000,'2026-01-15','2026-12-31','Accepted','2026-01-02'),
(2,1,2,'Auto',120000,'2026-01-15','2026-12-31','Accepted','2026-01-02'),
(3,1,1,'Auto',90000,'2026-01-15','2026-12-31','Pending','2026-01-02'),
(4,2,1,'Auto',150000,'2026-01-15','2026-12-31','Presented','2026-01-03'),
(5,2,2,'Auto',140000,'2026-01-15','2026-02-15','Expired','2026-01-03'),
(6,3,1,'Home',200000,'2026-02-15','2026-12-31','Accepted','2026-02-02'),
(7,3,1,'Home',210000,'2026-02-15','2026-12-31','Pending','2026-02-02'),
(8,4,2,'Umbrella',50000,'2026-02-15','2026-12-31','Declined','2026-02-02');
INSERT INTO quote_coverages VALUES
(1,1,30000000,NULL,'Identical terms'),(1,2,NULL,50000,'Identical terms'),
(2,1,30000000,NULL,'Identical terms'),(2,2,NULL,50000,'Identical terms'),
(3,1,30000000,NULL,'Identical terms'),(3,2,NULL,100000,'Different deductible'),
(4,1,30000000,NULL,'Different prospect'),(5,1,30000000,NULL,'Different prospect'),
(6,1,30000000,NULL,'Home'),(7,1,30000000,NULL,'Home'),
(8,1,100000000,NULL,'Umbrella');
