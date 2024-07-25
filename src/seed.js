console.log("SEEDING DATABASE ########################");

db = db.getSiblingDB("comiket");

db.createUser({
  user: process.env.MONGO_USERNAME,
  pwd: process.env.MONGO_PASSWORD,
  roles: [{ role: "readWrite", db: "comiket" }],
});

db.createCollection("users");
db.createCollection("doujin");

console.log("SEEDING COMPLETE ########################");
