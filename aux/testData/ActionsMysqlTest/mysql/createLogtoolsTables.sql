/*
*  To recreate the test database table structure, this can be 
*  executed by the user owning the database 'logfromtool'
*/

-- Server version	8.0.23
-- Dump completed on 2021-06-03 17:37:26

USE logfromtool; 

--
-- Table structure for table `EventTable`
--

DROP TABLE IF EXISTS `EventTable`;
CREATE TABLE `EventTable` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` varchar(40) NOT NULL,
  `application` varchar(30) DEFAULT NULL,
  `message` varchar(255) DEFAULT NULL,
  `date` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB
  AUTO_INCREMENT=5
  DEFAULT CHARSET=utf8mb4
          COLLATE=utf8mb4_0900_ai_ci;


--
-- Table structure for table `testOrmTable`
--

DROP TABLE IF EXISTS `testOrmTable`;
CREATE TABLE `testOrmTable` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` varchar(40) NOT NULL,
  `application` varchar(30) DEFAULT NULL,
  `message` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB
  AUTO_INCREMENT=3
  DEFAULT CHARSET=utf8mb4
          COLLATE=utf8mb4_0900_ai_ci;


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
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
          COLLATE=utf8mb4_0900_ai_ci;

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
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
          COLLATE=utf8mb4_0900_ai_ci;

