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
INSERT INTO `field_loc` VALUES ('5188e34c-5f5e-40b6-b1e8-3565e5f9d1a5','Montenegro','Kotor','Durmitor National Park',1650,'Meadow',43.0813,19.0832),('5c2400b7-9bdc-4567-8f5b-4352d76cc33e','Serbia','Belgrade','Avala Mountain',511,'Forest',44.6826,20.5079),('78cf9b2d-6406-4e02-bc71-f174a30a1b08','Bosnia','Federation of Bosnia','Bjelašnica Mountain',2067,'Rocky Terrain',43.6947,18.2703),('812f58d4-69a9-4e77-9c4e-4c4e4b3dbf63','Croatia','Split-Dalmatia','Biokovo Mountain',1762,'Alpine Meadow',43.3591,16.6772),('a61dfc17-7b04-4f8f-879f-59ed94427a89','North Macedonia','Ohrid','Galičica National Park',2255,'Alpine Forest',41.0805,20.8109);
/*!40000 ALTER TABLE `field_loc` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `image`
--

DROP TABLE IF EXISTS `image`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `image` (
  `image_id` varchar(50) NOT NULL,
  `specimen_id` varchar(50) DEFAULT NULL,
  `image_type` enum('field','herbarium','macro','microscope') DEFAULT NULL,
  `file_path` varchar(150) DEFAULT NULL,
  `width` int DEFAULT NULL,
  `height` int DEFAULT NULL,
  `upload_date` date DEFAULT NULL,
  PRIMARY KEY (`image_id`),
  KEY `specimen_id` (`specimen_id`),
  CONSTRAINT `image_ibfk_1` FOREIGN KEY (`specimen_id`) REFERENCES `specimen` (`specimen_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `image`
--

LOCK TABLES `image` WRITE;
/*!40000 ALTER TABLE `image` DISABLE KEYS */;
INSERT INTO `image` VALUES ('1df1cc80-be2a-499c-8bc6-a8b6f24b204e','22a9f0e3-7f63-45a1-9377-2d2f98f7fc68','field','images/22a9f0e3-7f63-45a1-9377-2d2f98f7fc68/R.jpg',1600,1197,'2023-04-30'),('250f4c52-6b37-451e-b340-2992d4579006','5ec6f1e6-5e6e-4855-b16f-02dcd6d1ed9c','field','images/5ec6f1e6-5e6e-4855-b16f-02dcd6d1ed9c/trifolium-incarnatum-fl-cevans-b.jpg',665,1000,'2023-04-30'),('90edbf98-b116-4611-9e21-81aeb33f3fd6','5ec6f1e6-5e6e-4855-b16f-02dcd6d1ed9c','field','images/5ec6f1e6-5e6e-4855-b16f-02dcd6d1ed9c/OIP.jpg',852,1136,'2023-04-30'),('951b1087-abd9-4166-99c1-6b8436239066','5ec6f1e6-5e6e-4855-b16f-02dcd6d1ed9c','field','images/5ec6f1e6-5e6e-4855-b16f-02dcd6d1ed9c/R.jpg',640,480,'2023-04-30'),('a3362ec5-6850-4095-b1de-e54e63208c2d','5ec6f1e6-5e6e-4855-b16f-02dcd6d1ed9c','field','images/5ec6f1e6-5e6e-4855-b16f-02dcd6d1ed9c/R (1).jpg',761,762,'2023-04-30'),('a93a8e9a-439a-4e87-ad50-c59d2e0af52f','20bdf63a-eeec-4b20-8d89-7cebb07a63df','field','images/20bdf63a-eeec-4b20-8d89-7cebb07a63df/hybridum.jpg',1000,750,'2023-04-30'),('b00818f8-e78e-4523-aacc-64cd4d1fa469','1d025af2-3f3c-45a6-9a10-e07c6b36be6b','field','images/1d025af2-3f3c-45a6-9a10-e07c6b36be6b/fragiferum.jpg',640,596,'2023-04-29'),('bab98b0e-806e-43c0-9c9f-05a8f13fe59e','a7d91c0e-27b7-4dd6-a33c-0ce6b0a6fb8d','field','images/a7d91c0e-27b7-4dd6-a33c-0ce6b0a6fb8d/R (2).jpg',600,800,'2023-04-30'),('e5aa1b86-15dc-4cda-86b2-b875572587a9','16e91f91-7638-4e19-bd07-bd4f1e6e7644','field','images/16e91f91-7638-4e19-bd07-bd4f1e6e7644/trifoliumrepens.jpg',1536,2048,'2023-04-29'),('e8bdaa4a-25de-4aa4-bc46-46de8080016e','5ec6f1e6-5e6e-4855-b16f-02dcd6d1ed9c','field','images/5ec6f1e6-5e6e-4855-b16f-02dcd6d1ed9c/Gardener_Clovers.jpg',640,480,'2023-04-30');
/*!40000 ALTER TABLE `image` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `plantnet_result`
--

DROP TABLE IF EXISTS `plantnet_result`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `plantnet_result` (
  `result_id` varchar(50) NOT NULL,
  `image_id` varchar(50) DEFAULT NULL,
  `best_match` varchar(150) DEFAULT NULL,
  `gbif_id` varchar(20) DEFAULT NULL,
  `score` float DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  PRIMARY KEY (`result_id`),
  KEY `image_id` (`image_id`),
  CONSTRAINT `plantnet_result_ibfk_1` FOREIGN KEY (`image_id`) REFERENCES `image` (`image_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `plantnet_result`
--

LOCK TABLES `plantnet_result` WRITE;
/*!40000 ALTER TABLE `plantnet_result` DISABLE KEYS */;
INSERT INTO `plantnet_result` VALUES ('0b2983b4-6d47-433b-80c9-283b0eea7ff3','90edbf98-b116-4611-9e21-81aeb33f3fd6','Trifolium incarnatum L.','5359378',0.94066,'2023-04-30 16:54:46'),('552e19e2-34aa-44d9-a773-5a842c4a60c5','e8bdaa4a-25de-4aa4-bc46-46de8080016e','Trifolium incarnatum L.','5359378',0.94468,'2023-04-30 16:54:10'),('7794144b-7300-4f45-97de-d87ad9cd79cd','a3362ec5-6850-4095-b1de-e54e63208c2d','Trifolium incarnatum L.','5359378',0.94717,'2023-04-30 15:04:48'),('80d86170-1730-4239-bbc0-3072773cb7e4','b00818f8-e78e-4523-aacc-64cd4d1fa469','Trifolium fragiferum L.','5358935',0.55242,'2023-04-29 19:32:33'),('894f7515-ba7d-439d-b87f-4a34376534a6','a93a8e9a-439a-4e87-ad50-c59d2e0af52f','Trifolium hybridum L.','6109535',0.77858,'2023-04-30 14:50:41'),('9a2bc7a0-5ede-41c4-9798-5e6bad9f11e4','bab98b0e-806e-43c0-9c9f-05a8f13fe59e','Trifolium incarnatum L.','5359378',0.97456,'2023-04-30 14:58:25'),('a2610304-0852-407f-bf23-e70c66d30478','951b1087-abd9-4166-99c1-6b8436239066','Trifolium incarnatum L.','5359378',0.95776,'2023-04-30 16:54:32'),('a8810675-f18d-4162-86ce-dfab642a7cba','250f4c52-6b37-451e-b340-2992d4579006','Trifolium incarnatum L.','5359378',0.98474,'2023-04-30 16:54:59'),('dc5d3b1e-c5b3-4440-9f82-a66951d97127','1df1cc80-be2a-499c-8bc6-a8b6f24b204e','Trifolium pratense L.','8324121',0.43416,'2023-04-30 14:55:35'),('ec0af8f1-d196-4fff-81ef-be22a26bd0e5','e5aa1b86-15dc-4cda-86b2-b875572587a9','Trifolium nigrescens Viv.','5358774',0.72321,'2023-04-29 19:28:45');
/*!40000 ALTER TABLE `plantnet_result` ENABLE KEYS */;
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
  `abstract` text,
  PRIMARY KEY (`pub_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `publication`
--

LOCK TABLES `publication` WRITE;
/*!40000 ALTER TABLE `publication` DISABLE KEYS */;
INSERT INTO `publication` VALUES ('02368f90-7cfa-4ca9-8b4d-4e4c3fb90dc4','10.1016/j.atmosenv.2020.117941','2021-02-01','Atmospheric Environment','Air Pollution and Human Health','Air pollution is a significant public health issue, contributing to respiratory and cardiovascular diseases and other health problems. This review summarizes the current understanding of the health impacts of air pollution and highlights the need for effective air pollution mitigation strategies.'),('238f1a81-d1da-44cf-8a2d-689764ef81f1','10.1016/j.biocon.2021.109099','2021-10-01','Biological Conservation','Conservation of Endangered Species in Fragmented Habitats','Fragmentation of natural habitats has led to increased extinction risk for many species. This study explores strategies for conserving endangered species in fragmented habitats, including habitat restoration and creation of habitat corridors.'),('2b73a216-d26f-4613-8a9d-cf9c1a6d36d7','10.1002/ece3.7759','2021-05-01','Ecology and Evolution','The Role of Microbes in Plant Health','Microbes play important roles in plant health, influencing nutrient uptake, disease resistance, and other factors. This review summarizes the current understanding of plant-microbe interactions and their implications for plant health.'),('31c8d623-0c2d-4f7b-a1e8-79dfc6f2be6f','10.1016/j.scitotenv.2020.137520','2020-12-15','Science of the Total Environment','Climate-driven increase in the occurrence of wildfires in the Mediterranean','We analyzed the frequency and intensity of wildfires across the Mediterranean and found that climate change has resulted in increased frequency and intensity of wildfires in the region.'),('3abfeee8-00a3-49a9-b157-5832e44063b4','10.1016/j.jenvman.2021.112704','2021-11-15','Journal of Environmental Management','Sustainable Management of Water Resources','Water is a critical resource for human and ecosystem health, but it is also under increasing pressure from population growth and climate change. This study explores strategies for sustainable management of water resources, including water conservation and watershed management.'),('3fb3e731-34d3-44f1-9da1-7730fa0b2c7f','10.1016/j.foreco.2021.119442','2021-12-01','Forest Ecology and Management','Effects of Forest Management on Biodiversity','Forest management practices can have significant impacts on biodiversity. This study examines the effects of different forest management strategies on biodiversity and highlights the importance of incorporating biodiversity conservation into forest management planning.'),('4b24cb4b-4c4b-4c81-82b3-7313d0743f8d','10.1126/science.abc5424','2020-08-28','Science','COVID-19 and the Global Environment','The COVID-19 pandemic has had a significant impact on the global environment, with reductions in greenhouse gas emissions and improved air and water quality in many regions. However, the pandemic has also led to increased use of single-use plastics and other environmental issues.'),('54f1515d-d11a-43d3-88a8-25af3e8893f1','10.1016/j.ecolind.2021.107571','2021-12-01','Ecological Indicators','Assessing Biodiversity in Forest Ecosystems','Biodiversity is an important indicator of ecosystem health, but assessing biodiversity can be challenging. This study examines the use of various indicators for assessing biodiversity in forest ecosystems and highlights the importance of integrating multiple indicators for effective biodiversity assessment.'),('6803c0b8-df75-47e1-8cc4-697b1c4d2875','10.1038/s41586-021-03738-2','2021-09-01','Nature','The Role of Seagrass in Carbon Sequestration','Seagrasses are important coastal ecosystems that can sequester significant amounts of carbon. This study quantifies the carbon sequestration potential of seagrass ecosystems and highlights the need for conservation and restoration of these habitats.'),('6f6723e3-6b8b-48c3-bd7f-1aa2bf1b3056','10.1038/s41558-021-01060-6','2021-10-01','Nature Climate Change','Climate Change and the Global Food System','Climate change is expected to have significant impacts on the global food system, including changes in crop yields and food security. This review summarizes the current state of knowledge on the interactions between climate change and the global food system.'),('8e80c0c1-6b9c-447c-8db7-6c75259b3d29','10.1021/acs.est.1c02491','2021-08-17','Environmental Science and Technology','Environmental Impacts of Single-Use Plastics','Single-use plastics have become a ubiquitous part of our daily lives, but their disposal has led to significant environmental impacts, including pollution of waterways and wildlife ingestion. This review summarizes the current state of knowledge on the environmental impacts of single-use plastics.');
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
INSERT INTO `publication_authors` VALUES ('0472f144-d0f3-44c7-946f-c8ecdf0d1661','9d1cb3db-3c90-4b62-b6b4-684ad57a4124','8e80c0c1-6b9c-447c-8db7-6c75259b3d29'),('4ad239a4-ef5b-4f5c-a306-128f9b1a2a4f','a3b8d514-37f5-4c75-9d67-9f9319e8aaf5','238f1a81-d1da-44cf-8a2d-689764ef81f1'),('c7fbbd1f-2f8b-46b6-a7b6-aa9e02d9c28e','a3b8d514-37f5-4c75-9d67-9f9319e8aaf5','31c8d623-0c2d-4f7b-a1e8-79dfc6f2be6f'),('3c4fdebc-4cb4-4c26-9c9c-cd36b1e482e2','c38a25e5-fa80-4a2a-94d1-0b14d9feadf4','8e80c0c1-6b9c-447c-8db7-6c75259b3d29'),('bf71f719-58e7-4652-946e-52df2cb46f84','e56fa2c3-3fb3-4b90-b7b6-ec8ba84dbaa4','8e80c0c1-6b9c-447c-8db7-6c75259b3d29'),('38cc3e3e-52a8-4750-94f1-54d369332117','e95a99c7-2da2-40c7-bf6e-69e8b11ec89e','238f1a81-d1da-44cf-8a2d-689764ef81f1'),('f285b79d-f34e-4e7b-8b28-200f666520b9','e95a99c7-2da2-40c7-bf6e-69e8b11ec89e','31c8d623-0c2d-4f7b-a1e8-79dfc6f2be6f'),('055580e6-1d6e-4c58-b69a-5365cf5b058f','f4310dc7-43cc-4d5e-a424-0b78d7b2f4ad','8e80c0c1-6b9c-447c-8db7-6c75259b3d29');
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
  `taxon_id` varchar(50) DEFAULT NULL,
  `subnomen` varchar(200) DEFAULT NULL,
  `field_loc_id` varchar(50) DEFAULT NULL,
  `storage_id` varchar(50) DEFAULT NULL,
  `collected_by` varchar(50) DEFAULT NULL,
  `verified_by` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`specimen_id`),
  UNIQUE KEY `reg_no` (`reg_no`),
  KEY `taxon_id` (`taxon_id`),
  KEY `field_loc_id` (`field_loc_id`),
  KEY `storage_id` (`storage_id`),
  KEY `collected_by` (`collected_by`),
  KEY `verified_by` (`verified_by`),
  CONSTRAINT `specimen_ibfk_1` FOREIGN KEY (`taxon_id`) REFERENCES `taxonomy` (`taxon_id`),
  CONSTRAINT `specimen_ibfk_2` FOREIGN KEY (`field_loc_id`) REFERENCES `field_loc` (`field_loc_id`),
  CONSTRAINT `specimen_ibfk_3` FOREIGN KEY (`storage_id`) REFERENCES `storage` (`storage_id`),
  CONSTRAINT `specimen_ibfk_4` FOREIGN KEY (`collected_by`) REFERENCES `users` (`user_id`),
  CONSTRAINT `specimen_ibfk_5` FOREIGN KEY (`verified_by`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `specimen`
--

LOCK TABLES `specimen` WRITE;
/*!40000 ALTER TABLE `specimen` DISABLE KEYS */;
INSERT INTO `specimen` VALUES ('16e91f91-7638-4e19-bd07-bd4f1e6e7644','S00003','2006-06-18','2006-06-19','aa49f0d5-53ed-44c2-9942-e89b5e5b9c5d','Trifolium repens','78cf9b2d-6406-4e02-bc71-f174a30a1b08','9f2ef7b1-0ee8-4f31-b69c-b98380a75f02','c38a25e5-fa80-4a2a-94d1-0b14d9feadf4','e56fa2c3-3fb3-4b90-b7b6-ec8ba84dbaa4'),('1d025af2-3f3c-45a6-9a10-e07c6b36be6b','S00002','2001-05-22','2001-05-23','0f8c53df-9d9a-41c1-bbe8-33c45ec03b48','Trifolium fragiferum','812f58d4-69a9-4e77-9c4e-4c4e4b3dbf63','7b46c2f9-d7a7-47c8-bc84-2b85a60f41d8','a3b8d514-37f5-4c75-9d67-9f9319e8aaf5','a41c0dd2-1d96-4c2c-bf1c-59a3d7dec813'),('20bdf63a-eeec-4b20-8d89-7cebb07a63df','SP0002','2023-04-02','2023-04-03','41fcf6a5-b864-47b7-9eb6-c8c7f21e9d3a','Trifolium hybridum.','812f58d4-69a9-4e77-9c4e-4c4e4b3dbf63','7b46c2f9-d7a7-47c8-bc84-2b85a60f41d8','a3b8d514-37f5-4c75-9d67-9f9319e8aaf5','a41c0dd2-1d96-4c2c-bf1c-59a3d7dec813'),('22a9f0e3-7f63-45a1-9377-2d2f98f7fc68','00270','2019-07-08','2019-07-10','5de0a4df-4d4c-4c7a-952d-0d4232f37ba3','Trifolium pratense','5188e34c-5f5e-40b6-b1e8-3565e5f9d1a5','9f2ef7b1-0ee8-4f31-b69c-b98380a75f02','6931e6d9-aa67-4d06-9a39-42af8b7756cf','f4310dc7-43cc-4d5e-a424-0b78d7b2f4ad'),('234d1e25-96d2-4d7f-b86e-956b9a0d2aa8','00271','2012-08-12','2012-08-13','41fcf6a5-b864-47b7-9eb6-c8c7f21e9d3a','Trifolium hybridum','812f58d4-69a9-4e77-9c4e-4c4e4b3dbf63','f37c2a25-963c-40ce-983e-28fc39c690d7','e56fa2c3-3fb3-4b90-b7b6-ec8ba84dbaa4','9d1cb3db-3c90-4b62-b6b4-684ad57a4124'),('2eafdd44-9d13-4f23-9a83-4c4b726d4ef4','1234','2001-05-12','2001-05-15','0f8c53df-9d9a-41c1-bbe8-33c45ec03b48','Trifolium fragiferum','a61dfc17-7b04-4f8f-879f-59ed94427a89','3df3b1d2-92cf-463a-9c1d-b7d8950ecfae','c38a25e5-fa80-4a2a-94d1-0b14d9feadf4','e95a99c7-2da2-40c7-bf6e-69e8b11ec89e'),('4a34d152-1cf0-4ea4-8c11-135d3604c3f2','2345','2002-06-20','2002-06-21','41fcf6a5-b864-47b7-9eb6-c8c7f21e9d3a','Trifolium hybridum','812f58d4-69a9-4e77-9c4e-4c4e4b3dbf63','7b46c2f9-d7a7-47c8-bc84-2b85a60f41d8','c38a25e5-fa80-4a2a-94d1-0b14d9feadf4','f4310dc7-43cc-4d5e-a424-0b78d7b2f4ad'),('4a67de45-3054-4e67-9783-0f9451c31d95','SP006','2007-08-12','2007-08-28','5de0a4df-4d4c-4c7a-952d-0d4232f37ba3','Trifolium pratense','a61dfc17-7b04-4f8f-879f-59ed94427a89','7b46c2f9-d7a7-47c8-bc84-2b85a60f41d8','e56fa2c3-3fb3-4b90-b7b6-ec8ba84dbaa4','6931e6d9-aa67-4d06-9a39-42af8b7756cf'),('5c41e5d7-90a9-41d8-b1d9-9880f82c0bfb','SP004','2005-07-18','2005-08-01','aa49f0d5-53ed-44c2-9942-e89b5e5b9c5d','Trifolium repens.','78cf9b2d-6406-4e02-bc71-f174a30a1b08','f37c2a25-963c-40ce-983e-28fc39c690d7','c38a25e5-fa80-4a2a-94d1-0b14d9feadf4','f4310dc7-43cc-4d5e-a424-0b78d7b2f4ad'),('5ec6f1e6-5e6e-4855-b16f-02dcd6d1ed9c','3456','2003-07-15','2003-07-20','4e1a29db-1e8e-4fa6-b34b-25c9371a0298','Trifolium incarnatum','78cf9b2d-6406-4e02-bc71-f174a30a1b08','9f2ef7b1-0ee8-4f31-b69c-b98380a75f02','a3b8d514-37f5-4c75-9d67-9f9319e8aaf5','c38a25e5-fa80-4a2a-94d1-0b14d9feadf4'),('73042e3c-24e9-4a9d-aeb2-72a29a2a83a1','SP005','2006-06-29','2006-07-15','4e1a29db-1e8e-4fa6-b34b-25c9371a0298','Trifolium incarnatum','5188e34c-5f5e-40b6-b1e8-3565e5f9d1a5','3df3b1d2-92cf-463a-9c1d-b7d8950ecfae','e56fa2c3-3fb3-4b90-b7b6-ec8ba84dbaa4','c38a25e5-fa80-4a2a-94d1-0b14d9feadf4'),('a7d91c0e-27b7-4dd6-a33c-0ce6b0a6fb8d','SP0003','2023-04-03','2023-04-04','4e1a29db-1e8e-4fa6-b34b-25c9371a0298','Trifolium incarnatum','78cf9b2d-6406-4e02-bc71-f174a30a1b08','9f2ef7b1-0ee8-4f31-b69c-b98380a75f02','c38a25e5-fa80-4a2a-94d1-0b14d9feadf4','e56fa2c3-3fb3-4b90-b7b6-ec8ba84dbaa4'),('ba58b749-ecf3-4b6a-a5c1-5b94f5b1af04','S00001','2002-07-12','2002-07-13','0f8c53df-9d9a-41c1-bbe8-33c45ec03b48','Trifolium fragiferum','a61dfc17-7b04-4f8f-879f-59ed94427a89','3df3b1d2-92cf-463a-9c1d-b7d8950ecfae','6931e6d9-aa67-4d06-9a39-42af8b7756cf','9d1cb3db-3c90-4b62-b6b4-684ad57a4124'),('e64a8b3d-0e5a-4a85-8d8d-0d9ebcb86e65','SP0001','2023-04-01','2023-04-02','0f8c53df-9d9a-41c1-bbe8-33c45ec03b48','Trifolium fragiferum','a61dfc17-7b04-4f8f-879f-59ed94427a89','3df3b1d2-92cf-463a-9c1d-b7d8950ecfae','6931e6d9-aa67-4d06-9a39-42af8b7756cf','9d1cb3db-3c90-4b62-b6b4-684ad57a4124'),('ffb37f52-406a-4d4f-a1f8-5c37a5e5faaa','00269','2015-06-21','2015-06-23','4e1a29db-1e8e-4fa6-b34b-25c9371a0298','Trifolium incarnatum','5c2400b7-9bdc-4567-8f5b-4352d76cc33e','7b46c2f9-d7a7-47c8-bc84-2b85a60f41d8','c38a25e5-fa80-4a2a-94d1-0b14d9feadf4','e56fa2c3-3fb3-4b90-b7b6-ec8ba84dbaa4');
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
INSERT INTO `specimen_publication` VALUES ('40cfe685-baa7-4666-9145-12f5a5c5c9e5','16e91f91-7638-4e19-bd07-bd4f1e6e7644','4b24cb4b-4c4b-4c81-82b3-7313d0743f8d'),('3b77eacb-2a87-4d19-9a9c-b7f9ec042e8d','16e91f91-7638-4e19-bd07-bd4f1e6e7644','8e80c0c1-6b9c-447c-8db7-6c75259b3d29'),('6c616fe6-5205-4847-9bbf-6e24429fa06e','1d025af2-3f3c-45a6-9a10-e07c6b36be6b','3fb3e731-34d3-44f1-9da1-7730fa0b2c7f'),('4a6a1a7e-6bf4-4d68-98cf-8d7dab6d24f6','22a9f0e3-7f63-45a1-9377-2d2f98f7fc68','6803c0b8-df75-47e1-8cc4-697b1c4d2875'),('7a2b46dc-e1f4-4a9d-9d12-cfb8814dfbb1','234d1e25-96d2-4d7f-b86e-956b9a0d2aa8','2b73a216-d26f-4613-8a9d-cf9c1a6d36d7'),('2a1c1579-6f95-4d2b-a579-82c99b129c57','234d1e25-96d2-4d7f-b86e-956b9a0d2aa8','6f6723e3-6b8b-48c3-bd7f-1aa2bf1b3056'),('6b29268a-f874-4325-bc7d-07102b20e496','5c41e5d7-90a9-41d8-b1d9-9880f82c0bfb','54f1515d-d11a-43d3-88a8-25af3e8893f1'),('4d4c1604-7f9a-45c2-a2e6-5547776e7b6f','73042e3c-24e9-4a9d-aeb2-72a29a2a83a1','3abfeee8-00a3-49a9-b157-5832e44063b4'),('83e31b17-1a89-4c63-a019-b2f7a61ca01d','ba58b749-ecf3-4b6a-a5c1-5b94f5b1af04','4b24cb4b-4c4b-4c81-82b3-7313d0743f8d'),('a203be7e-67c2-4d9d-b1d2-97a470af2f10','e64a8b3d-0e5a-4a85-8d8d-0d9ebcb86e65','2b73a216-d26f-4613-8a9d-cf9c1a6d36d7');
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
  `box` varchar(100) NOT NULL,
  `room` varchar(20) DEFAULT NULL,
  `shelf` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`storage_id`),
  UNIQUE KEY `box` (`box`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `storage`
--

LOCK TABLES `storage` WRITE;
/*!40000 ALTER TABLE `storage` DISABLE KEYS */;
INSERT INTO `storage` VALUES ('3df3b1d2-92cf-463a-9c1d-b7d8950ecfae','Box 1','Room A','Shelf 1'),('7b46c2f9-d7a7-47c8-bc84-2b85a60f41d8','Box 2','Room A','Shelf 2'),('9f2ef7b1-0ee8-4f31-b69c-b98380a75f02','Box 5','Room C','Shelf 5'),('adee6a95-6dab-4bcb-8b04-c6b3af7524c4','Box 3','Room B','Shelf 3'),('f37c2a25-963c-40ce-983e-28fc39c690d7','Box 4','Room B','Shelf 4');
/*!40000 ALTER TABLE `storage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `taxonomy`
--

DROP TABLE IF EXISTS `taxonomy`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `taxonomy` (
  `taxon_id` varchar(50) NOT NULL,
  `taxon_name` varchar(100) NOT NULL,
  `gbif_key` varchar(20) NOT NULL,
  `taxon_rank` enum('FORM','VARIETY','SUBSPECIES','SPECIES','GENUS','FAMILY','ORDER','CLASS','PHYLUM','KINGDOM') NOT NULL,
  `parent_taxon_key` varchar(50) DEFAULT NULL,
  `common_name` varchar(50) DEFAULT NULL,
  `authority` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`taxon_id`),
  UNIQUE KEY `gbif_key` (`gbif_key`),
  KEY `parent_taxon_key` (`parent_taxon_key`),
  CONSTRAINT `taxonomy_ibfk_1` FOREIGN KEY (`parent_taxon_key`) REFERENCES `taxonomy` (`taxon_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `taxonomy`
--

LOCK TABLES `taxonomy` WRITE;
/*!40000 ALTER TABLE `taxonomy` DISABLE KEYS */;
INSERT INTO `taxonomy` VALUES ('0f2b5e5e-59a1-4db2-a2e9-6d31b0111ea5','Magnoliopsida','220','CLASS','f7a6aefe-4cb4-4d0c-8587-6c506d6fa73f','Dicots',NULL),('0f8c53df-9d9a-41c1-bbe8-33c45ec03b48','Trifolium fragiferum','5358935','SPECIES','f4a4d4fb-7604-4f7a-8d8f-82eae55cc3c3','Strawberry clover','L.'),('41fcf6a5-b864-47b7-9eb6-c8c7f21e9d3a','Trifolium hybridum','6109535','SPECIES','f4a4d4fb-7604-4f7a-8d8f-82eae55cc3c3','Alsike clover','L.'),('4e1a29db-1e8e-4fa6-b34b-25c9371a0298','Trifolium incarnatum','5359378','SPECIES','f4a4d4fb-7604-4f7a-8d8f-82eae55cc3c3','Crimson clover','L.'),('5de0a4df-4d4c-4c7a-952d-0d4232f37ba3','Trifolium pratense','8324121','SPECIES','f4a4d4fb-7604-4f7a-8d8f-82eae55cc3c3','Red Clover','L.'),('69b711d6-87ea-4c8e-a58a-5e0c46e5715e','Plantae','6','KINGDOM',NULL,'Plants',NULL),('aa49f0d5-53ed-44c2-9942-e89b5e5b9c5d','Trifolium repens','5358748','SPECIES','f4a4d4fb-7604-4f7a-8d8f-82eae55cc3c3','White clover','L.'),('ce5d6f5b-4f1b-4ea7-b35d-8c8af42b1bb9','Trifolium arvense','5359246','SPECIES','f4a4d4fb-7604-4f7a-8d8f-82eae55cc3c3','Rabbitfoot clover','L.'),('ee8baf51-f20c-40f1-91da-7a38a4ec4d4c','Fabaceae','5018','FAMILY','f6a4691f-dc1d-4a2b-a8e3-3c5b5dc5b5d5','Pea Family',NULL),('f4a4d4fb-7604-4f7a-8d8f-82eae55cc3c3','Trifolium','5342','GENUS','ee8baf51-f20c-40f1-91da-7a38a4ec4d4c','Clovers',NULL),('f6a4691f-dc1d-4a2b-a8e3-3c5b5dc5b5d5','Rosales','3858','ORDER','0f2b5e5e-59a1-4db2-a2e9-6d31b0111ea5','Rosids',NULL),('f7a6aefe-4cb4-4d0c-8587-6c506d6fa73f','Embryophyta','58003','PHYLUM','69b711d6-87ea-4c8e-a58a-5e0c46e5715e','Land Plants',NULL);
/*!40000 ALTER TABLE `taxonomy` ENABLE KEYS */;
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
INSERT INTO `users` VALUES ('6931e6d9-aa67-4d06-9a39-42af8b7756cf','Kelly','Kapoor','kelly.kapoor@example.com','$2y$12$zS6pIvEegNUlFk1ivdx77ur4yNp5f05X5Nso1z/sZG5r/UaLqMB1W',1,0),('9d1cb3db-3c90-4b62-b6b4-684ad57a4124','Ryan','Howard','ryan.howard@example.com','$2y$12$8L1FYt3vCtBxswcn7KT.LObRRiWAmnYAJQZ1nV/vQPMGViurWV7vK',1,0),('a3b8d514-37f5-4c75-9d67-9f9319e8aaf5','Jim','Halpert','jim.halpert@example.com','$2y$12$xZsWKLg8WWvzDuxKJFQ05OsEG6gsxUQNdffLrLbK.w0AV3DCcXzIm',1,1),('a41c0dd2-1d96-4c2c-bf1c-59a3d7dec813','Kevin','Malone','user@example.com','473287f8298dba7163a897908958f7c0eae733e25d2e027992ea2edc9bed2fa8',1,1),('c38a25e5-fa80-4a2a-94d1-0b14d9feadf4','Dwight','Schrute','dwight.schrute@example.com','$2y$12$7.Fg43N8W/u7Gssd/0uOFOPoNpXEpUI5iqzVkPXdZXrZG5C1cJW0G',1,0),('e56fa2c3-3fb3-4b90-b7b6-ec8ba84dbaa4','Angela','Martin','angela.martin@example.com','$2y$12$C.AZJknlU6CnU6d2y6xgJOpT9sG02imM1ylN.NZ6f54pN8Oa6U/2W',1,0),('e95a99c7-2da2-40c7-bf6e-69e8b11ec89e','Pam','Beesly','pam.beesly@example.com','$2y$12$MUoA6XkzMzgLyDEONsw/e.y2jK/PigJxg.mtjJG7cFQH/fMqr9OjK',1,0),('f4310dc7-43cc-4d5e-a424-0b78d7b2f4ad','Michael','Scott','michael.scott@example.com','$2y$12$CllrIRvM/cPDrWkXy6KjVO6JFv0f28MZ6lAUCZsJAJpCY0vzB0FnW',1,0);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `weather`
--

DROP TABLE IF EXISTS `weather`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `weather` (
  `weather_id` varchar(50) NOT NULL,
  `specimen_id` varchar(50) DEFAULT NULL,
  `mean_temperature` float DEFAULT NULL,
  `humidity` float DEFAULT NULL,
  `precipitation` float DEFAULT NULL,
  `wind_speed` float DEFAULT NULL,
  `wind_direction` float DEFAULT NULL,
  PRIMARY KEY (`weather_id`),
  UNIQUE KEY `specimen_id` (`specimen_id`),
  CONSTRAINT `weather_ibfk_1` FOREIGN KEY (`specimen_id`) REFERENCES `specimen` (`specimen_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `weather`
--

LOCK TABLES `weather` WRITE;
/*!40000 ALTER TABLE `weather` DISABLE KEYS */;
INSERT INTO `weather` VALUES ('9d30deeb-3d6e-4e31-9fa8-7beb173185bf','16e91f91-7638-4e19-bd07-bd4f1e6e7644',15.6,49,2.5,2.34,232);
/*!40000 ALTER TABLE `weather` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-04-30 20:29:43
