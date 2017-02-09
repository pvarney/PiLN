-- phpMyAdmin SQL Dump
-- version 4.2.12deb2+deb8u2
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Feb 08, 2017 at 10:53 PM
-- Server version: 5.5.53-0+deb8u1
-- PHP Version: 5.6.29-0+deb8u1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `PiLN`
--

-- --------------------------------------------------------

--
-- Table structure for table `Firing`
--

CREATE TABLE IF NOT EXISTS `Firing` (
  `run_id` int(11) NOT NULL DEFAULT '0',
  `segment` int(11) NOT NULL DEFAULT '0',
  `datetime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `set_temp` decimal(8,2) NOT NULL,
  `temp` decimal(8,2) NOT NULL,
  `int_temp` decimal(8,2) DEFAULT NULL,
  `pid_output` decimal(8,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `Profiles`
--

CREATE TABLE IF NOT EXISTS `Profiles` (
`run_id` int(11) NOT NULL,
  `state` varchar(25) NOT NULL DEFAULT 'Staged',
  `notes` text,
  `start_time` timestamp NULL DEFAULT NULL,
  `end_time` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `Segments`
--

CREATE TABLE IF NOT EXISTS `Segments` (
  `run_id` int(11) NOT NULL,
  `segment` int(11) NOT NULL,
  `set_temp` int(11) NOT NULL,
  `rate` int(11) NOT NULL,
  `hold_min` int(11) NOT NULL,
  `int_sec` int(11) NOT NULL,
  `start_time` timestamp NULL DEFAULT NULL,
  `end_time` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `Firing`
--
ALTER TABLE `Firing`
 ADD PRIMARY KEY (`run_id`,`segment`,`datetime`);

--
-- Indexes for table `Profiles`
--
ALTER TABLE `Profiles`
 ADD PRIMARY KEY (`run_id`);

--
-- Indexes for table `Segments`
--
ALTER TABLE `Segments`
 ADD PRIMARY KEY (`run_id`,`segment`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `Profiles`
--
ALTER TABLE `Profiles`
MODIFY `run_id` int(11) NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=34;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
