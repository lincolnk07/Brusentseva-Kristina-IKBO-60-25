#!/bin/sh
set -eu

if [ "$#" -gt 1 ]; then
    echo "Usage: $0 [dotnet-executable]" >&2
    exit 2
fi

dotnet=${1:-dotnet}
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
framework=net8.0
temporary_root=$(mktemp -d "${TMPDIR:-/tmp}/nuget-graph-compare.XXXXXX")
trap 'rm -rf "$temporary_root"' EXIT HUP INT TERM

compare_package() {
    name=$1
    package=$2
    version=$3
    declared_child=$4
    project_dir="$temporary_root/$name"
    mkdir -p "$project_dir"
    cat > "$project_dir/Compare.csproj" <<EOF_PROJECT
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>$framework</TargetFramework>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="$package" Version="$version" />
  </ItemGroup>
</Project>
EOF_PROJECT

    echo "=== $package $version ($framework): root graph ==="
    "$dotnet" restore "$project_dir" -p:NuGetAudit=false
    "$dotnet" nuget why "$project_dir" "$package" \
        --framework "$framework"
    python3 "$script_dir/print_assets_order.py" \
        "$project_dir/obj/project.assets.json" "$framework"
    echo "=== Query of declared child $declared_child ==="
    "$dotnet" nuget why "$project_dir" "$declared_child" \
        --framework "$framework"
}

compare_package newtonsoft Newtonsoft.Json 13.0.4 NETStandard.Library
compare_package serilog Serilog 4.4.0 \
    System.Diagnostics.DiagnosticSource
compare_package nunit NUnit 5.0.0 System.Threading.Tasks.Extensions
