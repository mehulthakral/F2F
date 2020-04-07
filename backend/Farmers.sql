CREATE TABLE CONSUMER(
	CONSID int,
    CONSNAME varchar(50),
	CONSPASS varchar(50),
	CONSLOC varchar(200),
	PRIMARY KEY(CONSID)
	);

CREATE TABLE FARMER(
	FARMID int,
    FARMNAME varchar(50),
	FARMPASS varchar(50),
	FARMLOC varchar(200),
	PRIMARY KEY(FARMID)
	);
	
CREATE TABLE PRODUCT(
	PRODID int,
    PRODTITLE varchar(50),
	PRODDESC varchar(1000),
	PRODTYPE varchar(50),
	UPLOADTIME varchar(50),
	OWNERID int,
	PRICE bigint,
	MAXQUANT bigint,
	MINBUYQUANT bigint,
	FOREIGN KEY(OWNERID) REFERENCES FARMER(FARMID) ON DELETE CASCADE ON UPDATE CASCADE,
	PRIMARY KEY(PRODID)
	);
	
CREATE TABLE CART(
	CONSID int,
    PRODID int,
	QUANTITY int,
	FOREIGN KEY(CONSID) REFERENCES CONSUMER(CONSID) ON DELETE CASCADE ON UPDATE CASCADE,
	FOREIGN KEY(PRODID) REFERENCES PRODUCT(PRODID) ON DELETE CASCADE ON UPDATE CASCADE,
	PRIMARY KEY(CONSID,PRODID)
	);
	
CREATE TABLE SALES(
	SALEID int,
	CONSID int,
    PRODID int,
	QUANTITY int,
	BUYTIME varchar(50),
	FOREIGN KEY(CONSID) REFERENCES CONSUMER(CONSID) ON DELETE CASCADE ON UPDATE CASCADE,
	FOREIGN KEY(PRODID) REFERENCES PRODUCT(PRODID) ON DELETE CASCADE ON UPDATE CASCADE,
	PRIMARY KEY(SALEID,CONSID,PRODID)
	);
	
CREATE TABLE REVIEW(
	REVIEWID int,
	REVIEWERID int,
    PRODID int,
	REVIEWDESC varchar(1000),
	REVIEWSTAR FLOAT,
	REVIEWTIME varchar(50),
	VERIFIED int,
	FOREIGN KEY(REVIEWERID) REFERENCES CONSUMER(CONSID) ON DELETE CASCADE ON UPDATE CASCADE,
	FOREIGN KEY(PRODID) REFERENCES PRODUCT(PRODID) ON DELETE CASCADE ON UPDATE CASCADE,
	PRIMARY KEY(REVIEWID)
	);
	
CREATE TABLE IMAGE(
	IMAGEID int,
    PRODID int,
	IMAGENAME varchar(1000),
	IMAGEPATH varchar(500),
	IMAGEX varchar(50),
	FOREIGN KEY(PRODID) REFERENCES PRODUCT(PRODID) ON DELETE CASCADE ON UPDATE CASCADE,
	PRIMARY KEY(IMAGEID)
	);
	
CREATE TABLE DEALS(
	DEALID int AUTO_INCREMENT,
    PRODID int,
	NEWPRICE int,
	DISCOUNT_PERCENT int,
	FOREIGN KEY(PRODID) REFERENCES PRODUCT(PRODID) ON DELETE CASCADE ON UPDATE CASCADE,
	PRIMARY KEY(DEALID,PRODID)
	);