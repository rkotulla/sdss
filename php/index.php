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

$all_dirs = scandir('../', SCANDIR_SORT_ASCENDING);
//print_r($all_dirs);
$objects = array();
foreach ($all_dirs as $item) {
    $testdir = "../".$item;
    if ($item == "." || $item == "..") {
        continue;
    }
    if (is_dir($testdir)) {
        $objects[] = $item;
    }
}
//print_r($objects);
sort($objects);

$current_obj = array_search($objname, $objects);
//print($current_obj);
//print($objects[$current_obj]);
//var_dump($gauss);
//var_dump($median);

$before_after=4;
if ($current_obj == 0) {
    $prev = "";
    $iprev = 0;
} else {
    $prev = $objects[$current_obj-1];
    $iprev = $current_obj-$before_after;
    if ($iprev < 0) {
        $iprev = 0;
    }
}

if ($current_obj == count($objects)-1) {
    $next = "";
    $inext = count($objects)-1;
} else {
    $next = $objects[$current_obj+1];
    $inext = $current_obj+$before_after;
    if ($inext >= count($objects)) {
        $inext = count($objects)-1;
    }
}
?>




<html>
<head>
    <link rel="stylesheet" type="text/css" href="../reu_sdss.css">
    <base target="_blank">
    <!-- This is the php version -->
</head>
<body>

<div class="navigate_head">
    <div class='prev'><a href="../<?=$prev?>" target="_self">Previous</a></div>
    <div class='next'><a href="../<?=$next?>" target="_self">Next</a></div>
    <div class="navigate">
    <?php
        for ($i=$iprev;$i<=$inext; $i++) {
            ?>
            <span class="link"><a href="../<?=$objects[$i]?>" target="_self"><?=$objects[$i]?></a></span>
            <?php
        }
    ?>
    </div>
</div>

</div>
<h1><?= $objname ?></h1>
<p><ul>
    <li><a href="https://ned.ipac.caltech.edu/cgi-bin/objsearch?objname=<?= $objname ?>&extend=no&hconst=73&omegam=0.27&omegav=0.73&corr_z=1&out_csys=Equatorial&out_equinox=J2000.0&obj_sort=RA+or+Longitude&of=pre_text&zv_breaker=30000.0&list_limit=5&img_stamp=YES">NED page</a></li>
    <li><a href="https://ned.ipac.caltech.edu/cgi-bin/NEDatt?objname=<?= $objname ?>">NED classifications</a></li>
    <li><a href="https://ned.ipac.caltech.edu/cgi-bin/imgdata?objname=<?= $objname ?>&hconst=73.0&omegam=0.27&omegav=0.73&corr_z=1">NED images</a></li>
    <!--<li><a href="https://ned.ipac.caltech.edu/cgi-bin/datasearch?search_type=Photo_id&objid=58481&objname=IC0494&img_stamp=YES&hconst=73.0&omegam=0.27&omegav=0.73&corr_z=1&of=table">NED Spectral Energy Distributions</a></li>-->
    <li><a href="http://simbad.u-strasbg.fr/simbad/sim-id?Ident=<?= $objname ?>&NbIdent=1&Radius=2&Radius.unit=arcmin&submit=submit+id">SIMBad Identifier query</a></li>
    <li><a href="http://hla.stsci.edu/hlaview.html#Inventory|filterText%3D%24filterTypes%3D|query_string=<?=$objname?>&posfilename=&poslocalname=&posfilecount=&listdelimiter=whitespace&listformat=degrees&RA=&Dec=&Radius=0.015000&inst-control=all&inst=ACS&inst=ACSGrism&inst=WFC3&inst=WFPC2&inst=NICMOS&inst=NICGRISM&inst=COS&inst=WFPC2-PC&inst=STIS&inst=FOS&inst=GHRS&imagetype=best&prop_id=&spectral_elt=&proprietary=both&preview=1&output_size=256&cutout_size=12.8|ra=&dec=&sr=&level=&image=&inst=ACS%2CACSGrism%2CWFC3%2CWFPC2%2CNICMOS%2CNICGRISM%2CCOS%2CWFPC2-PC%2CSTIS%2CFOS%2CGHRS&ds=">Search Hubble Legacy Archive</a></li>
    <li><a href="http://adsabs.harvard.edu/cgi-bin/nph-abs_connect?db_key=AST&db_key=PRE&qform=AST&arxiv_sel=astro-ph&arxiv_sel=cond-mat&arxiv_sel=cs&arxiv_sel=gr-qc&arxiv_sel=hep-ex&arxiv_sel=hep-lat&arxiv_sel=hep-ph&arxiv_sel=hep-th&arxiv_sel=math&arxiv_sel=math-ph&arxiv_sel=nlin&arxiv_sel=nucl-ex&arxiv_sel=nucl-th&arxiv_sel=physics&arxiv_sel=quant-ph&arxiv_sel=q-bio&sim_query=YES&ned_query=YES&adsobj_query=YES&aut_logic=OR&obj_logic=OR&author=&object=<?=$objname?>&start_mon=&start_year=&end_mon=&end_year=&ttl_logic=OR&title=&txt_logic=OR&text=&nr_to_return=200&start_nr=1&jou_pick=ALL&ref_stems=&data_and=ALL&group_and=ALL&start_entry_day=&start_entry_mon=&start_entry_year=&end_entry_day=&end_entry_mon=&end_entry_year=&min_score=&sort=SCORE&data_type=SHORT&aut_syn=YES&ttl_syn=YES&txt_syn=YES&aut_wt=1.0&obj_wt=1.0&ttl_wt=0.3&txt_wt=3.0&aut_wgt=YES&obj_wgt=YES&ttl_wgt=YES&txt_wgt=YES&ttl_sco=YES&txt_sco=YES&version=1">ADS Object search</a></li>
</ul>
</p>

<div class="filtered">
    <h2><?= $objname ?> - gri stack</h2>
    <p>full frame: <a href='<?= $objname ?>_gri.jpg'><?= $objname ?>_gri.jpg</a><br>
        <a href='<?= $objname ?>_gri.crop.jpg'><img src='<?= $objname ?>_gri.crop.jpg' style='width: 500px;'</img></a>
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

