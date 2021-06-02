/*
*  Restore values in tables to permit testing logjoin;
*  values dumped on 2021-06-03 18:01:45
*/

-- MySQL dump 10.13  Distrib 8.0.23, for Linux (x86_64)
-- Server version	8.0.23


--
-- Restoring data for table `EventTable`
--

LOCK TABLES `EventTable` WRITE;
INSERT INTO `EventTable` VALUES (1,'picsou','compta','Je suis radin','01/01/2020'),(2,'gaetan','bar','je suis le cousin','21/12/1960'),(3,'bill','nginx:latest','Voyons','12/05/2021'),(4,'donald','nginx:latest','Big lie?','12/05/2021');
UNLOCK TABLES;

--
-- Restoring data for table `testOrmTable`
--

LOCK TABLES `testOrmTable` WRITE;
INSERT INTO `testOrmTable` VALUES (1,'toto','mail','attention au spam'),(2,'titi','voice','attention glo-minet');
UNLOCK TABLES;

--
-- Restoring data for table `testTable`
--

LOCK TABLES `testTable` WRITE;
INSERT INTO `testTable` VALUES (1,'2021-04-28','nginx:latest','A','blaba'),(2,'2021-04-28',NULL,'B','bidule'),(3,NULL,'nginx:latest','C',NULL),(4,NULL,'nginx:latest','Z','Zorro'),(5,NULL,NULL,'1',NULL),(6,NULL,NULL,'0',NULL);
UNLOCK TABLES;


