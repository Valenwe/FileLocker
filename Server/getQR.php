<?php
require_once("./BACKEND/server.php");


if (empty($_SESSION["private_passphrase"]))
    header("location: index.php");
?>

<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="X-UA-Compatible" content="ie=edge" />
    <link rel="stylesheet" href="getQR.css" />
    <link href="assets/img/favicon.png" rel="icon">
    <title>Save QR</title>

    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/5.0.0-alpha1/css/bootstrap.min.css" integrity="sha384-r4NyP46KrjDleawBgD5tp8Y7UzmLA05oM1iAEQ17CSuDqnUK2+k9luXQOfXJCJ4I" crossorigin="anonymous">
    <link href="assets/css/main.css" rel="stylesheet">
</head>

<body>
    <video autoplay muted loop id="campfire">
        <source src=".\assets\img\campfire.mp4" type="video/mp4">
    </video>
    <h1 class="title">Sauvegardez !</h1>
    <div class="img_qr">
        <img src="<?php echo $_SESSION["a2f_url"]; ?>">
    </div>
    <div class="flexbox">
        <h4 class="txt">Scannez ce QR code avec une application d'authentification comme Google Authenticator</h4>
        <h4 class="txt">Sauvegarder le code ci-dessous, vous en aurez besoin à chaque première utilisation du logiciel</h4>
    </div>

    <div class="passphrase">
        <h4 class="pv_phrase"><?php echo implode(" ", str_split($_SESSION["private_passphrase"], 4)); ?></h4>
    </div>

    <div class="flexbox">
        <a href="./assets/installer/Installer_FileLocker.exe"><button class="start_btn">Téléchargez notre logiciel !</button></a>
    </div>

</body>