<?php
/**
 * Created by PhpStorm.
 * User: rkotulla
 * Date: 7/8/16
 * Time: 9:26 AM
 */


$all_dirs = scandir('.', SCANDIR_SORT_ASCENDING);
//print_r($all_dirs);
$objects = array();
foreach ($all_dirs as $item) {
    $testdir = $item;
    if ($item == "." || $item == "..") {
        continue;
    }
    if (is_dir($testdir)) {
        $objects[] = $item;
    }
}
//print_r($objects);
sort($objects);
//print_r($objects);

$filtered = [".crop", '.filtered.gauss_003.0.crop', '.filtered.gauss_015.0.crop'];
?>

    <html>
    <head>
        <link rel="stylesheet" type="text/css" href="reu_sdss.css">
        <base target="_blank">
        <!-- This is the php version -->
        <title>Galaxy Overview -- REU Project: Early-type galaxies with peculiarities</title>
    </head>
<body>

<?php
foreach ($objects as $objname) {
    $thumb = sprintf("%s/%s_gri.crop.jpg", $objname, $objname);


    $comment_fn = sprintf("%s/comment.txt", $objname);
    //print($comment_fn);
    $comment = ""; //$comment_fn."<br>";
    if (is_file($comment_fn)) {
        $comment .= file_get_contents($comment_fn);
    } else {
        $comment .= "NO COMMENTS";
    }

    ?>

    <a href="<?=$objname?>" target="_blank"><h1 class="summary"><?=$objname?></h1></a>
    <?php
        foreach ($filtered as $img_fn) {
            $full_img_fn = sprintf("%s/%s_gri%s.jpg", $objname, $objname, $img_fn);
            ?>
            <img src="<?=$full_img_fn?>" class="summary">
            <?php
        }
    ?>

    <pre class="summary"><?=$comment?></pre>

    <?php

}

?>

</body></html>

