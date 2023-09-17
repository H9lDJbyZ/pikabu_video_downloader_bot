-- files definition

CREATE TABLE files (
	"id" INTEGER NOT NULL UNIQUE, 
    "link_page" TEXT NOT NULL,
    "message_id" INTEGER NOT NULL,
    PRIMARY KEY("id" AUTOINCREMENT)
);

-- process definition

CREATE TABLE "process" (
	"id"	INTEGER NOT NULL UNIQUE,
	"status_id"	INTEGER NOT NULL DEFAULT 0, 
    "link_page" TEXT NOT NULL, 
    "from_id" INTEGER NOT NULL, 
    "message_id" INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);