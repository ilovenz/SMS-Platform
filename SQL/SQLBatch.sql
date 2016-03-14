mysql -u root -pHelloAlex < /home/alex/SourceCode/SMS/SQL/CreateTables.sql

mysql -u root -pHelloAlex < /home/alex/SourceCode/SMS/SQL/spGenerateSMS.sql
mysql -u root -pHelloAlex < /home/alex/SourceCode/SMS/SQL/spSetServerInService.sql
mysql -u root -pHelloAlex < /home/alex/SourceCode/SMS/SQL/spServerRegistration.sql
mysql -u root -pHelloAlex < /home/alex/SourceCode/SMS/SQL/spSetSMStoSend.sql
mysql -u root -pHelloAlex < /home/alex/SourceCode/SMS/SQL/spGetSMStoSend.sql


