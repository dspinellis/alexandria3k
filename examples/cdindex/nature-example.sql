-- Report the CD5 index of example papers
-- Kohn and Sham 10.1103/PhysRev.140.A1133 (reported in Nature as -0.22)
-- Watson Crick 10.1038/171737a0 (reported in Nature as 0.62)

SELECT doi,cdindex
FROM rolap.cdindex
WHERE doi IN ('10.1103/physrev.140.a1133', '10.1038/171737a0');
