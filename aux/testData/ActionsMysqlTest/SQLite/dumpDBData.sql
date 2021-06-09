-- MySQL dump 10.13  Distrib 8.0.23, for Linux (x86_64)
-- Hand Simplified to use with Sqlite
-- Host: 172.19.0.2    Database: logfromtool
-- ------------------------------------------------------
-- Server version	8.0.23

--
-- Table structure for table `EventTable`
--

DROP TABLE IF EXISTS `EventTable`;
CREATE TABLE `EventTable` (
  `id` int NOT NULL,
  `user_id` varchar(40) NOT NULL,
  `application` varchar(30) DEFAULT NULL,
  `message` varchar(255) DEFAULT NULL,
  `date` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
);


--
-- Dumping data for table `EventTable`
--
INSERT INTO `EventTable` VALUES (1,'picsou','compta','Je suis radin','01/01/2020'),(2,'gaetan','bar','je suis le cousin','21/12/1960'),(3,'bill','nginx:latest','Voyons','12/05/2021'),(4,'donald','nginx:latest','Big lie?','12/05/2021'),(5,'asterix','alpine:latest','village gaulois','7/7/2021'),(6,'idefix','alpine:3.13','petit chien','7/7/2021');
/*!40000 ALTER TABLE `EventTable` ENABLE KEYS */;

--
-- Table structure for table `testOrmTable`
--

DROP TABLE IF EXISTS `testOrmTable`;
CREATE TABLE `testOrmTable` (
  `id` int NOT NULL,
  `user_id` varchar(40) NOT NULL,
  `application` varchar(30) DEFAULT NULL,
  `message` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
);

--
-- Dumping data for table `testOrmTable`
--

INSERT INTO `testOrmTable` VALUES (1,'toto','mail','attention au spam'),(2,'titi','voice','attention glo-minet');


--
-- Table structure for table `testTable`
--

DROP TABLE IF EXISTS `testTable`;
CREATE TABLE `testTable` (
  `idtestTable` int NOT NULL,
  `date` date DEFAULT NULL,
  `application` varchar(45) DEFAULT NULL,
  `priority` varchar(45) DEFAULT NULL,
  `Message` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`idtestTable`)
); 

--
-- Dumping data for table `testTable`
--

INSERT INTO `testTable` VALUES (1,'2021-04-28','nginx:latest','A','blaba'),(2,'2021-04-28',NULL,'B','bidule'),(3,NULL,'nginx:latest','C',NULL),(4,NULL,'nginx:latest','Z','Zorro'),(5,NULL,NULL,'1',NULL),(6,NULL,NULL,'0',NULL),(7,'2021-06-07','alpine:latest','BB','Hum added alpine:latest'),(8,'2021-06-07','alpine:3.12','AA','alpine 3.12'),(9,'2021-06-07','alpine:3.13','AA','alpine 3.13');


--
-- Table structure for table `tree`
--


DROP TABLE IF EXISTS `tree`;
CREATE TABLE `tree` (
  `id` int NOT NULL,
  `parent_id` int DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `nval` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ;

-- This table is filled by running the tests
-- No data here


-- Dump completed on 2021-06-07 12:04:38
