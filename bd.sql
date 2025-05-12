<<<<<<< HEAD
DROP TABLE IF EXISTS `holidays`;
CREATE TABLE IF NOT EXISTS `holidays` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `name` varchar(151) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=218 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `purple_day`
--

DROP TABLE IF EXISTS `purple_day`;
CREATE TABLE IF NOT EXISTS `purple_day` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `new_date` date NOT NULL,
  `weekday` int NOT NULL,
  `status` enum('Confirmed','Canceled','Changed') DEFAULT 'Confirmed',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=169 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
=======
DROP TABLE IF EXISTS `holidays`;
CREATE TABLE IF NOT EXISTS `holidays` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `name` varchar(151) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=218 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `purple_day`
--

DROP TABLE IF EXISTS `purple_day`;
CREATE TABLE IF NOT EXISTS `purple_day` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date` date NOT NULL,
  `new_date` date NOT NULL,
  `weekday` int NOT NULL,
  `status` enum('Confirmed','Canceled','Changed') DEFAULT 'Confirmed',
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=169 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE IF NOT EXISTS `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
>>>>>>> 8a9ca94 (Salva alterações locais antes de rebase)
