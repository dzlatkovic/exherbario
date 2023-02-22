-- MySQL dump 10.13  Distrib 8.0.31, for Win64 (x86_64)
--
-- Host: localhost    Database: herbarium
-- ------------------------------------------------------
-- Server version	8.0.31

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `field_loc`
--

DROP TABLE IF EXISTS `field_loc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `field_loc` (
  `field_loc_id` varchar(50) NOT NULL,
  `country` varchar(20) DEFAULT NULL,
  `region` varchar(20) DEFAULT NULL,
  `locality` varchar(40) DEFAULT NULL,
  `altitude` int DEFAULT NULL,
  `habitat` varchar(20) DEFAULT NULL,
  `gps_lat` float DEFAULT NULL,
  `gps_long` float DEFAULT NULL,
  PRIMARY KEY (`field_loc_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `field_loc`
--

LOCK TABLES `field_loc` WRITE;
/*!40000 ALTER TABLE `field_loc` DISABLE KEYS */;
INSERT INTO `field_loc` VALUES ('088ea826-cbd3-4d9d-b685-8c5ecb5c93ad','Serbia','Niš','Suva Mt.',1400,'wood',43.25,22.03),('12e2d668-072a-4a9e-bde5-404f4140005a','Greece','Thessaloniki','Peraia',0,'beach',40.507,22.92),('27d6dd52-8702-4b93-9935-76d6f4057fee','Serbia','Niš','urban area',20,'park',43.32,21.9),('395c0852-0348-4b71-b05e-462321c5e54e','Serbia','Kosovo','Šara Mt.',100,'wood',42.39,21.57),('5d4fd21e-c061-42d8-80d4-1949f41a72e8','Serbia','Pirot','Staničenje',200,'wood',43.2,22.514),('7b74fff3-1f5e-47de-a55b-14febe71586a','Serbia','Niš','Hum',150,'pasture',43.37,21.9),('8d5f9189-f85e-4f5e-89c3-51fa6878f273','Serbia','Jablanički','Lipovica',0,'field',43.13,21.89),('9b26646b-f75a-444e-91e9-1e7e83d03c37','Austria','Styria','Graz',100,'urban area',47.05,15.46),('a8db55fa-92d7-4155-b6da-1d281e649aa3','Serbia','Vojvodina','Slano Kopovo',100,'swamp',45.61,20.21),('aa353840-4818-4e38-b275-3fe0854a81e6','Serbia','Šumadija','Grabovac',100,'wood',43.91,20.76),('ad89502b-0863-446a-a79a-16a4a3dd9032','Greece','Thessaloniki','Kalamaria',10,'park',40.64,22.93),('b2ab6a0c-d0e2-4fce-8572-76f8a3f245e7','Serbia','Niš','urban area',50,'park',43.31,21.91),('ca69800d-21b2-4f12-961f-48ac829c204d','Serbia','Pirot','Zavojsko lake',15,'wood',43.24,22.64),('dc44c8ba-2c86-4a68-b289-d497ece8f2f7','Serbia','Toplica','Kuršumlija',150,'urban area',43.13,21.28),('e5a9c5a5-16f6-4584-85e8-e30dd0eb0b42','Serbia','Pirot','Stara Mt.',1200,'wood',43.29,22.7);
/*!40000 ALTER TABLE `field_loc` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `photos`
--

DROP TABLE IF EXISTS `photos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `photos` (
  `photos_id` varchar(50) NOT NULL,
  `field_photo` varchar(200) DEFAULT NULL,
  `specimen_photo` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`photos_id`),
  UNIQUE KEY `field_photo` (`field_photo`),
  UNIQUE KEY `specimen_photo` (`specimen_photo`),
  CONSTRAINT `photos_chk_1` CHECK ((`field_photo` <> `specimen_photo`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `photos`
--

LOCK TABLES `photos` WRITE;
/*!40000 ALTER TABLE `photos` DISABLE KEYS */;
INSERT INTO `photos` VALUES ('000fddff-dfb1-4a16-8f01-9a24f345e491','field6.jpg','specimen6.jpg'),('04c4cf55-fef0-45d8-a748-1b7f8a091d50','field8.jpg','specimen8.jpg'),('0858f2aa-00e0-4eff-afd6-cbac79729aa9','field15.jpg','specimen15.jpg'),('0ec0ec7d-55f5-4b19-97d0-0b3cd2e631f9','field11.jpg','specimen11.jpg'),('1bde4dc7-ca4e-4eef-8df2-568d43d84f01','field17.jpg','specimen17.jpg'),('25c45214-16c6-4a16-b295-fb21b205121f','field9.jpg','specimen9.jpg'),('3ae66645-3b05-4edf-beca-19354fed092c','field14.jpg','specimen14.jpg'),('430a07d4-2e0d-4514-b46d-37905de6ecb0','field4.jpg','specimen4.jpg'),('469a86a4-923f-47d9-9def-dc7c7868619c','field13.jpg','specimen13.jpg'),('4fd0493a-d895-482a-afa0-34d88d2f6181','field1.jpg','specimen1.jpg'),('516cba54-d2f1-429c-b53d-59b10645f884','field5.jpg','specimen5.jpg'),('743733a7-71f7-42cb-abd6-fc71356c6b87','field16.jpg','specimen16.jpg'),('91abcded-8230-4e4d-bf48-b5242ad32fee','field18.jpg','specimen18.jpg'),('9243ff52-7d31-4308-8c71-dd6a9f6cdb40','field3.jpg','specimen3.jpg'),('93e3af18-67d1-4f3f-bb04-e5a031e9345a','field20.jpg','specimen20.jpg'),('a8dc9e9c-a7a5-4223-9157-d80c5d2deeb6','field7.jpg','specimen7.jpg'),('ab195cc7-a4d6-477b-8e90-94a4586672f6','field19.jpg','specimen19.jpg'),('b7d88c8a-ea77-4683-acf8-0f75f139fe45','field10.jpg','specimen10.jpg'),('d75e84d0-cc96-4e16-81b9-d1c5a0fdada5','field21.jpg','specimen21.jpg'),('e9ee493c-109f-4dfe-9a45-155e1dfc14a2','field2.jpg','specimen2.jpg'),('fa283ef3-0c33-498d-a2ce-086713309127','field12.jpg','specimen12.jpg');
/*!40000 ALTER TABLE `photos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `publication`
--

DROP TABLE IF EXISTS `publication`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `publication` (
  `pub_id` varchar(50) NOT NULL,
  `doi` varchar(200) NOT NULL,
  `year` date DEFAULT NULL,
  `journal` varchar(100) DEFAULT NULL,
  `title` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`pub_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `publication`
--

LOCK TABLES `publication` WRITE;
/*!40000 ALTER TABLE `publication` DISABLE KEYS */;
INSERT INTO `publication` VALUES ('1a491644-976b-4a86-9460-ec9765fa938d','10.7890/qrst.2019.005','2019-01-01','Journal of Simulated Studies','Simulation and Its Applications in Mock Research'),('1b997bfc-f02c-458a-aec7-7a0d8518bafa','10.5879/erty.2010.001','1991-01-01','Journal of Imaginary Sciences','The Impact of Hypothetical Scenarios on Fictive Behaviors'),('8a1594cd-bc6d-4239-87a8-b62715c4facf','10.5678/efgh.2022.002','2022-01-01','Journal of Fictitious Research','Examining the Effects of Pretend Variables on Mock Outcomes'),('f4e2f757-cb88-410e-b8a9-84912993061f','10.1234/abcd.2023.001','2023-01-01','Journal of Mock Studies','An Analysis of Mock Data'),('f668258b-6d7c-4eb0-b262-07d3aed56557','10.3456/mnop.2020.004','2020-01-01','Journal of Nonexistent Phenomena','Investigating the Characteristics of Imaginary Participants'),('f6850293-5abc-4190-90b6-99b15b9f7bd0','10.2345/uvwx.2018.006','2018-01-01','Journal of Made-Up Sciences','A Study of Fabricated Data and Its Implications for Mock Research');
/*!40000 ALTER TABLE `publication` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `publication_authors`
--

DROP TABLE IF EXISTS `publication_authors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `publication_authors` (
  `publication_authors_id` varchar(50) NOT NULL,
  `user_id` varchar(50) DEFAULT NULL,
  `publication_id` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`publication_authors_id`),
  UNIQUE KEY `publication_authors_uc` (`user_id`,`publication_id`),
  KEY `publication_id` (`publication_id`),
  CONSTRAINT `publication_authors_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `publication_authors_ibfk_2` FOREIGN KEY (`publication_id`) REFERENCES `publication` (`pub_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `publication_authors`
--

LOCK TABLES `publication_authors` WRITE;
/*!40000 ALTER TABLE `publication_authors` DISABLE KEYS */;
INSERT INTO `publication_authors` VALUES ('d3ede2c3-a1c9-4e0e-b0f5-1eef62377b06','181488bc-722b-4ad0-9d21-83ef569720e1','1a491644-976b-4a86-9460-ec9765fa938d'),('da3d27a8-4769-43d7-97ff-5eb0ae59cb16','181488bc-722b-4ad0-9d21-83ef569720e1','f4e2f757-cb88-410e-b8a9-84912993061f'),('c9917163-0596-434e-847b-5f1a3e29808a','181488bc-722b-4ad0-9d21-83ef569720e1','f6850293-5abc-4190-90b6-99b15b9f7bd0'),('58ff500f-1803-42f2-bd69-151a449c7386','6f756ee3-0fb0-45f3-a905-a9a910f33ce6','1a491644-976b-4a86-9460-ec9765fa938d'),('23970663-cffa-4ec8-99a2-82d7765cefa7','6f756ee3-0fb0-45f3-a905-a9a910f33ce6','f4e2f757-cb88-410e-b8a9-84912993061f'),('17689a31-fd77-427c-8fdd-c8a62bf6f64a','6f756ee3-0fb0-45f3-a905-a9a910f33ce6','f668258b-6d7c-4eb0-b262-07d3aed56557'),('2077034e-72a4-446a-81bf-4e4f860f6b6a','6f756ee3-0fb0-45f3-a905-a9a910f33ce6','f6850293-5abc-4190-90b6-99b15b9f7bd0'),('c224cf99-7683-485a-aad4-b421164257b1','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c','1a491644-976b-4a86-9460-ec9765fa938d'),('4533df72-f609-4e55-aa33-d98edeb16717','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c','1b997bfc-f02c-458a-aec7-7a0d8518bafa'),('84a9486d-eda9-43a1-99a5-7041b821c0c5','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c','8a1594cd-bc6d-4239-87a8-b62715c4facf'),('60fb80c8-2747-43d3-b3be-6f99282c2f5d','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c','f6850293-5abc-4190-90b6-99b15b9f7bd0');
/*!40000 ALTER TABLE `publication_authors` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `specimen`
--

DROP TABLE IF EXISTS `specimen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `specimen` (
  `specimen_id` varchar(50) NOT NULL,
  `reg_no` varchar(10) NOT NULL,
  `collection_date` date DEFAULT NULL,
  `reg_date` date DEFAULT NULL,
  `family` varchar(50) DEFAULT NULL,
  `genus` varchar(50) DEFAULT NULL,
  `species` varchar(50) DEFAULT NULL,
  `subnomen` varchar(200) DEFAULT NULL,
  `field_loc_id` varchar(50) DEFAULT NULL,
  `storage_id` varchar(50) DEFAULT NULL,
  `photos_id` varchar(50) DEFAULT NULL,
  `collected_by` varchar(50) DEFAULT NULL,
  `verified_by` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`specimen_id`),
  UNIQUE KEY `reg_no` (`reg_no`),
  UNIQUE KEY `photos_id` (`photos_id`),
  KEY `field_loc_id` (`field_loc_id`),
  KEY `storage_id` (`storage_id`),
  KEY `collected_by` (`collected_by`),
  KEY `verified_by` (`verified_by`),
  CONSTRAINT `specimen_ibfk_1` FOREIGN KEY (`field_loc_id`) REFERENCES `field_loc` (`field_loc_id`),
  CONSTRAINT `specimen_ibfk_2` FOREIGN KEY (`storage_id`) REFERENCES `storage` (`storage_id`),
  CONSTRAINT `specimen_ibfk_3` FOREIGN KEY (`photos_id`) REFERENCES `photos` (`photos_id`),
  CONSTRAINT `specimen_ibfk_4` FOREIGN KEY (`collected_by`) REFERENCES `users` (`user_id`),
  CONSTRAINT `specimen_ibfk_5` FOREIGN KEY (`verified_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `specimen`
--

LOCK TABLES `specimen` WRITE;
/*!40000 ALTER TABLE `specimen` DISABLE KEYS */;
INSERT INTO `specimen` VALUES ('0b0d716f-30fb-4e0d-8c96-436786f9246a','020','2020-04-04','2020-04-10','Asteraceae','Blumea','balsamifera','Blumea balsamifera (L.) DC.','b2ab6a0c-d0e2-4fce-8572-76f8a3f245e7','53095394-1ae2-428d-a4c2-f3b52751877a','ab195cc7-a4d6-477b-8e90-94a4586672f6','181488bc-722b-4ad0-9d21-83ef569720e1','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c'),('34c9e0b4-85e7-4a41-a5c7-b76900920801','008','2021-07-11','2021-08-11','Fagaceae','Quercus','toumeyi','Quercus toumeyi Sarg.','a8db55fa-92d7-4155-b6da-1d281e649aa3','53095394-1ae2-428d-a4c2-f3b52751877a','d75e84d0-cc96-4e16-81b9-d1c5a0fdada5','6f756ee3-0fb0-45f3-a905-a9a910f33ce6','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c'),('3a48220a-85bf-408e-8d5b-791da5f28803','002','2019-03-10','2019-05-22','Asteraceae','Blumea','lacera','Blumea lacera (Burm. f.) DC.','27d6dd52-8702-4b93-9935-76d6f4057fee','0a3562ae-8b5a-47e8-9a47-51d84dc6adde','04c4cf55-fef0-45d8-a748-1b7f8a091d50','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c'),('3f9b13fe-db6a-4444-ac3a-002e3ae79348','005','1999-04-11','1999-05-11','Asteraceae','Blumea','lacera','Blumea lacera (Burm. f.) DC.','7b74fff3-1f5e-47de-a55b-14febe71586a','e833413c-a68e-44e4-b380-fb0e81048ab9','516cba54-d2f1-429c-b53d-59b10645f884','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c','6f756ee3-0fb0-45f3-a905-a9a910f33ce6'),('42d7d4ce-3a69-430d-9b82-c6a337826d6f','001','2015-02-10','2015-02-22','Plantaginaceae','Plantago','sparsiflora','Plantago sparsiflora Michx.','088ea826-cbd3-4d9d-b685-8c5ecb5c93ad','0a3562ae-8b5a-47e8-9a47-51d84dc6adde','25c45214-16c6-4a16-b295-fb21b205121f','181488bc-722b-4ad0-9d21-83ef569720e1','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c'),('4383b9ae-8778-4d39-9440-4f54baf670de','004','2022-05-10','2022-06-11','Asteraceae','Blumea','lacera','Blumea lacera (Burm. f.) DC.','5d4fd21e-c061-42d8-80d4-1949f41a72e8','53095394-1ae2-428d-a4c2-f3b52751877a','000fddff-dfb1-4a16-8f01-9a24f345e491','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c','6f756ee3-0fb0-45f3-a905-a9a910f33ce6'),('51914074-1a38-438b-8934-043d6da4939a','003','2014-10-10','2014-10-11','Asteraceae','Blumea','lacera','Blumea lacera (Burm. f.) DC.','395c0852-0348-4b71-b05e-462321c5e54e','0a3562ae-8b5a-47e8-9a47-51d84dc6adde','a8dc9e9c-a7a5-4223-9157-d80c5d2deeb6','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c'),('714c0448-c748-4bbd-84a5-e02f87b0fd09','022','2018-05-04','2019-05-10','Asteraceae','Blumea','tenella','Blumea tenella DC.','ca69800d-21b2-4f12-961f-48ac829c204d','0a3562ae-8b5a-47e8-9a47-51d84dc6adde','1bde4dc7-ca4e-4eef-8df2-568d43d84f01','181488bc-722b-4ad0-9d21-83ef569720e1','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c'),('852bba4f-5155-4a63-80c5-2d26fc975215','006','2000-04-11','2000-05-11','Rosaceae','Rubus','vermontanus','Rubus vermontanus Blanch.','8d5f9189-f85e-4f5e-89c3-51fa6878f273','53095394-1ae2-428d-a4c2-f3b52751877a','430a07d4-2e0d-4514-b46d-37905de6ecb0','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c','6f756ee3-0fb0-45f3-a905-a9a910f33ce6'),('877bae4c-b730-4934-a99f-5996725db82f','025','2016-08-08','2017-01-02','Asteraceae','Achillea','clavennea','Achillea clavennae L.','dc44c8ba-2c86-4a68-b289-d497ece8f2f7','e833413c-a68e-44e4-b380-fb0e81048ab9','3ae66645-3b05-4edf-beca-19354fed092c','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c'),('c7e36ac3-33a9-4e8c-acb1-e7d27d0f3eae','009','2020-06-11','2020-06-11','Asteraceae','Rudbeckia','occidentalis','Rudbeckia occidentalis Nutt.','a8db55fa-92d7-4155-b6da-1d281e649aa3','53095394-1ae2-428d-a4c2-f3b52751877a','93e3af18-67d1-4f3f-bb04-e5a031e9345a','6f756ee3-0fb0-45f3-a905-a9a910f33ce6','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c'),('cd2b115c-8086-433e-a235-7b1c96d855f1','023','2017-06-06','2017-06-11','Fabaceae','Astragalus','scopulorum','Astragalus scopulorum Porter','b2ab6a0c-d0e2-4fce-8572-76f8a3f245e7','0a3562ae-8b5a-47e8-9a47-51d84dc6adde','743733a7-71f7-42cb-abd6-fc71356c6b87','6f756ee3-0fb0-45f3-a905-a9a910f33ce6','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c'),('dc280779-524a-4cd3-b38a-b3bcc67c2a68','021','2019-04-04','2019-04-10','Asteraceae','Blumea','flava','Blumea flava DC.','ca69800d-21b2-4f12-961f-48ac829c204d','0a3562ae-8b5a-47e8-9a47-51d84dc6adde','91abcded-8230-4e4d-bf48-b5242ad32fee','181488bc-722b-4ad0-9d21-83ef569720e1','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c'),('e3f16b10-9f96-42dc-9652-c7ff2672eb6e','024','2017-02-02','2017-02-02','Asteraceae','Blumea','riparia','Blumea riparia DC.','ca69800d-21b2-4f12-961f-48ac829c204d','0a3562ae-8b5a-47e8-9a47-51d84dc6adde','0858f2aa-00e0-4eff-afd6-cbac79729aa9','6f756ee3-0fb0-45f3-a905-a9a910f33ce6','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c'),('e560112f-8144-47dc-92d7-c8bb5d110dc9','019','2020-04-04','2020-04-10','Lamiaceae','Phyllostegia','waimeae','Phyllostegia waimeae Wawra','aa353840-4818-4e38-b275-3fe0854a81e6','e833413c-a68e-44e4-b380-fb0e81048ab9','e9ee493c-109f-4dfe-9a45-155e1dfc14a2','6f756ee3-0fb0-45f3-a905-a9a910f33ce6','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c'),('ec1c2313-997c-48f8-831e-d1a1b87a8453','026','2020-05-01','2020-05-04','Asteraceae','Achillea','millefolium','Achillea millefolium L.','088ea826-cbd3-4d9d-b685-8c5ecb5c93ad','0a3562ae-8b5a-47e8-9a47-51d84dc6adde','fa283ef3-0c33-498d-a2ce-086713309127','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c','181488bc-722b-4ad0-9d21-83ef569720e1'),('f4dfc49c-47c8-4e1a-aec8-74c7a4f54a7c','007','2022-04-11','2022-05-11','Fabaceae','Vicia','faba','Vicia faba L.','9b26646b-f75a-444e-91e9-1e7e83d03c37','e833413c-a68e-44e4-b380-fb0e81048ab9','9243ff52-7d31-4308-8c71-dd6a9f6cdb40','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c','a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c');
/*!40000 ALTER TABLE `specimen` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `specimen_publication`
--

DROP TABLE IF EXISTS `specimen_publication`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `specimen_publication` (
  `specimen_publication_id` varchar(50) NOT NULL,
  `specimen_id` varchar(50) DEFAULT NULL,
  `publication_id` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`specimen_publication_id`),
  UNIQUE KEY `publication_authors_uc` (`specimen_id`,`publication_id`),
  KEY `publication_id` (`publication_id`),
  CONSTRAINT `specimen_publication_ibfk_1` FOREIGN KEY (`specimen_id`) REFERENCES `specimen` (`specimen_id`),
  CONSTRAINT `specimen_publication_ibfk_2` FOREIGN KEY (`publication_id`) REFERENCES `publication` (`pub_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `specimen_publication`
--

LOCK TABLES `specimen_publication` WRITE;
/*!40000 ALTER TABLE `specimen_publication` DISABLE KEYS */;
INSERT INTO `specimen_publication` VALUES ('d52be018-72de-47c5-8bde-faf0b9bb1bd2','34c9e0b4-85e7-4a41-a5c7-b76900920801','8a1594cd-bc6d-4239-87a8-b62715c4facf'),('cf0fc939-09a2-4ced-a349-5f82da8e6072','42d7d4ce-3a69-430d-9b82-c6a337826d6f','f4e2f757-cb88-410e-b8a9-84912993061f'),('9c875ebc-d7f4-4279-9c89-0c12322b887c','51914074-1a38-438b-8934-043d6da4939a','1b997bfc-f02c-458a-aec7-7a0d8518bafa'),('2b771290-c2f7-438d-8f6c-04901bf5c752','51914074-1a38-438b-8934-043d6da4939a','f6850293-5abc-4190-90b6-99b15b9f7bd0'),('3ad3b5f7-6d7c-4e4c-8996-309785d45ab8','714c0448-c748-4bbd-84a5-e02f87b0fd09','1b997bfc-f02c-458a-aec7-7a0d8518bafa'),('a240bc99-037b-460f-aa8f-43ae4b080a5c','877bae4c-b730-4934-a99f-5996725db82f','1a491644-976b-4a86-9460-ec9765fa938d'),('346be938-be11-46a4-bd78-20d5ea4ede11','cd2b115c-8086-433e-a235-7b1c96d855f1','8a1594cd-bc6d-4239-87a8-b62715c4facf'),('b4c0e7ed-1854-4ddb-8c71-9e69f9fb9a0b','f4dfc49c-47c8-4e1a-aec8-74c7a4f54a7c','f668258b-6d7c-4eb0-b262-07d3aed56557');
/*!40000 ALTER TABLE `specimen_publication` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `storage`
--

DROP TABLE IF EXISTS `storage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `storage` (
  `storage_id` varchar(50) NOT NULL,
  `room` varchar(20) DEFAULT NULL,
  `shelf` varchar(20) DEFAULT NULL,
  `box` varchar(100) NOT NULL,
  PRIMARY KEY (`storage_id`),
  UNIQUE KEY `box` (`box`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `storage`
--

LOCK TABLES `storage` WRITE;
/*!40000 ALTER TABLE `storage` DISABLE KEYS */;
INSERT INTO `storage` VALUES ('0a3562ae-8b5a-47e8-9a47-51d84dc6adde','112','3','13B'),('53095394-1ae2-428d-a4c2-f3b52751877a','112','1','12A'),('e833413c-a68e-44e4-b380-fb0e81048ab9','112','2','14C');
/*!40000 ALTER TABLE `storage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` varchar(50) NOT NULL,
  `name` varchar(50) DEFAULT NULL,
  `surname` varchar(50) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `password` varchar(200) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `is_superuser` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES ('181488bc-722b-4ad0-9d21-83ef569720e1','Pam','Beesly','pam@example.com','473287f8298dba7163a897908958f7c0eae733e25d2e027992ea2edc9bed2fa8',1,0),('6f756ee3-0fb0-45f3-a905-a9a910f33ce6','John','Smith','john@example.com','473287f8298dba7163a897908958f7c0eae733e25d2e027992ea2edc9bed2fa8',1,1),('a6cf9caf-e2d6-4a6c-b725-e4cd92df5b0c','Aca','Lukas','aca@example.com','473287f8298dba7163a897908958f7c0eae733e25d2e027992ea2edc9bed2fa8',1,0);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-02-22 16:36:45
