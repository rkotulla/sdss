<?php
/**
 * Created by PhpStorm.
 * User: rkotulla
 * Date: 7/6/16
 * Time: 2:24 PM
 */

// Get current object name from directory name
$full_dir = getcwd();
$chunks = explode('/', $full_dir);
$objname = $chunks[count($chunks)-1];

$gauss = glob("*.filtered.gauss_*.crop.jpg");
$median = glob("*.filtered.median_*.crop.jpg");

//var_dump($gauss);
//var_dump($median);
?>




<html>
<head>
    <link rel="stylesheet" type="text/css" href="../reu_sdss.css">
    <base target="_blank">
    <!-- This is the php version -->
</head>
<body>

<h1><?= $objname ?></h1>
<p><ul>
    <li><a href="https://ned.ipac.caltech.edu/cgi-bin/objsearch?objname=<?= $objname ?>&extend=no&hconst=73&omegam=0.27&omegav=0.73&corr_z=1&out_csys=Equatorial&out_equinox=J2000.0&obj_sort=RA+or+Longitude&of=pre_text&zv_breaker=30000.0&list_limit=5&img_stamp=YES">NED page</a></li>
    <li><a href="https://ned.ipac.caltech.edu/cgi-bin/NEDatt?objname=<?= $objname ?>">NED classifications</a></li>
    <li><a href="https://ned.ipac.caltech.edu/cgi-bin/imgdata?objname=<?= $objname ?>&hconst=73.0&omegam=0.27&omegav=0.73&corr_z=1">NED images</a></li>
    <!--<li><a href="https://ned.ipac.caltech.edu/cgi-bin/datasearch?search_type=Photo_id&objid=58481&objname=IC0494&img_stamp=YES&hconst=73.0&omegam=0.27&omegav=0.73&corr_z=1&of=table">NED Spectral Energy Distributions</a></li>-->
    <li><a href="http://simbad.u-strasbg.fr/simbad/sim-id?Ident=<?= $objname ?>&NbIdent=1&Radius=2&Radius.unit=arcmin&submit=submit+id">SIMBad Identifier query</a></li>
</ul>
</p>

<div class="filtered">
    <h2><?= $objname ?> - gri stack</h2>
    <p>full frame: <a href='<?= $objname ?>_gri.jpg'><?= $objname ?>_gri.jpg</a><br>
        <a href='<?= $objname ?>_gri.crop.jpg'><img src='<?= $objname ?>_gri.crop.jpg' style='width:500;'</img></a>
    </p>
</div><hr>

<?php
 // Loop over all filtered files and create div blocks with data and images

$lists = [
    'gauss' => $gauss,
    'median' => $median,
    ];
//var_dump($lists);

foreach ($lists as $mode => $croplist) {

    //var_dump($croplist);
    foreach ($croplist as $cropped_fn) {
        $full_fn = str_replace(".crop", "", $cropped_fn);
        $beyond_objname = substr($cropped_fn, strlen($objname));
        preg_match_all('!\d+(?:\.\d+)?!', $beyond_objname, $matches);
        $sizes = array_map('floatval', $matches[0]);
        //var_dump($sizes);
        //print $full_fn;
        ?>

        <div class="filtered"><h2><?= $objname ?> - <?=$mode?> @ <?=sprintf("%.1f",$sizes[0])?> pixels</h2>
            <p>full frame: <a href='<?= $full_fn ?>'><?= $full_fn ?></a><br>
                <a href='<?=$cropped_fn?>'><img src='<?=$cropped_fn?>' style='width:500;'</img></a></p></div>


        <?php

    }
}
?>

</body></html>

