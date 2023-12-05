CREATE TABLE `FollowedArtist` (
  `id` int NOT NULL AUTO_INCREMENT,
  `artist_id` VARCHAR(25) NOT NULL,
  `guild_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `artist_id` (`artist_id`),
  KEY `guild_id` (`guild_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

INSERT INTO FollowedArtist (artist_id, guild_id)
SELECT artist_id, guild_id
FROM Artists;

CREATE TEMPORARY TABLE TempArtists AS
SELECT MIN(entry_id) AS pk, artist_id
FROM Artists
GROUP BY artist_id;

DELETE FROM Artists
WHERE entry_id NOT IN (SELECT pk FROM TempArtists);

DROP TEMPORARY TABLE TempArtists;

ALTER TABLE Artists CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE Artists DROP PRIMARY KEY, DROP COLUMN entry_id;
ALTER TABLE Artists CHANGE artist_id id VARCHAR(25) NOT NULL;
ALTER TABLE Artists DROP COLUMN role_id, DROP COLUMN guild_id;
ALTER TABLE Artists ADD PRIMARY KEY (id);

ALTER TABLE Guilds CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
ALTER TABLE Guilds CHANGE guild_id id bigint NOT NULL;
ALTER TABLE Guilds CHANGE channel_id music_channel_id bigint NOT NULL;

ALTER TABLE FollowedArtist
ADD CONSTRAINT FollowedArtist_ibfk_1
FOREIGN KEY (artist_id) REFERENCES Artists(id);

ALTER TABLE FollowedArtist
ADD CONSTRAINT FollowedArtist_ibfk_2
FOREIGN KEY (guild_id) REFERENCES Guilds(id);
