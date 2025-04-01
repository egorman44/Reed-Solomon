//////////////////////
// compilation "6.0.0"
// test        "3.6.0"
//////////////////////

//val chiselVersion = "6.0.0"
val chiselVersion = "3.6.0"

if(chiselVersion == "6.0.0"){
  ThisBuild / scalaVersion     := "2.13.12"
} else {
  ThisBuild / scalaVersion     := "2.13.8"
}

// Define the appropriate plugin conditionally
val chiselPlugin = if (chiselVersion == "6.0.0") {
  "org.chipsalliance" % "chisel-plugin" % chiselVersion cross CrossVersion.full
} else {
  "edu.berkeley.cs" % "chisel3-plugin" % chiselVersion cross CrossVersion.full
}

ThisBuild / version          := "0.1.0"
ThisBuild / organization     := "com.github.egorman44"


lazy val root = (project in file("."))
  .settings(
    name := "chisel-lib",
    libraryDependencies ++= {
      if(chiselVersion == "6.0.0") {
        Seq(
          "com.typesafe.play" %% "play-json" % "2.9.2",
          "org.chipsalliance" %% "chisel" % chiselVersion,
          "org.scalatest" %% "scalatest" % "3.2.16" % "test",
          "com.github.scopt" %% "scopt" % "4.0.1",
        ),
      } else {
        Seq(
          "com.typesafe.play" %% "play-json" % "2.9.2",
          "edu.berkeley.cs" %% "chisel3" % chiselVersion,
          "edu.berkeley.cs" %% "chiseltest" % "0.6.2" % "test",
          "org.scalatest" %% "scalatest" % "3.2.16" % "test",
          "com.github.scopt" %% "scopt" % "4.0.1",
        ),
      }

      },
    scalacOptions ++= Seq(
      "-language:reflectiveCalls",
      "-deprecation",
      "-feature",
      "-Xcheckinit",
      "-Ymacro-annotations",
    ),

    addCompilerPlugin(chiselPlugin),
    Compile / run / fork := true,
    Compile / run / javaOptions ++= Seq(
      "-Dproject.root=" + baseDirectory.value
    ),
    Test / fork := true,
    Test / javaOptions ++= Seq(
      "-Dproject.root=" + baseDirectory.value
    )
  )
