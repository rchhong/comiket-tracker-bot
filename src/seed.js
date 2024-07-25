console.log("SEEDING DATABASE ########################");

db = db.getSiblingDB(process.env.MONGO_DB_NAME);

db.createUser({
  user: process.env.MONGO_USERNAME,
  pwd: process.env.MONGO_PASSWORD,
  roles: [{ role: "readWrite", db: process.env.MONGO_DB_NAME }],
});

db.createCollection("users");
db.createCollection("doujins");

console.log("SEEDING COMPLETE ########################");
